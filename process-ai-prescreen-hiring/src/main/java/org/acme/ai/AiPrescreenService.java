package org.acme.ai;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.acme.candidate.Candidate;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class AiPrescreenService {

    private static final Logger logger = LoggerFactory.getLogger(AiPrescreenService.class);

    private static final List<String> REQUIRED_FIELDS = Arrays.asList(
            "email", "phone", "skills", "experience", "education");

    @RestClient
    AdkRestClient adk;

    // No defaultValue — these MUST be supplied via environment variables.
    // Set ADK_AUTH_USERNAME, ADK_AUTH_PASSWORD, and ADK_TENANT_NAME in your .env file
    // (see .env.example). Omitting them causes a clear startup failure rather than
    // silently using stale credentials.
    @ConfigProperty(name = "adk.auth.username")
    String adkUsername;

    @ConfigProperty(name = "adk.auth.password")
    String adkPassword;

    @ConfigProperty(name = "adk.tenant.name")
    String adkTenantName;

    private final ObjectMapper mapper = new ObjectMapper();
    private String cachedToken;
    private String cachedAgentId;

    public void prescreenCandidate(Candidate candidate) {
        logger.info(">>> AI Pre-Screening (agentic) for candidate: {} (via wx.O Prescreen Agent)",
                candidate.getFullName());

        try {
            String token = getToken();
            String agentId = getAgentId(token);
            String auth = "Bearer " + token;

            String message = buildPrompt(candidate);

            ObjectNode body = mapper.createObjectNode();
            body.putObject("message").put("role", "user").put("content", message);
            body.put("agent_id", agentId);

            JsonNode run = adk.createRun(auth, body);
            String runId = run.get("run_id").asText();
            String threadId = run.get("thread_id").asText();
            logger.info("ADK thread: {} — open http://localhost:4321/v1/threads/{}/messages",
                    threadId, threadId);

            // Poll for completion
            String status = "";
            for (int i = 0; i < 30; i++) {
                Thread.sleep(2000);
                status = adk.getRunStatus(auth, runId).get("status").asText();
                if ("completed".equals(status) || "failed".equals(status) || "cancelled".equals(status)) {
                    break;
                }
            }

            if (!"completed".equals(status)) {
                logger.error("Run did not complete in time, status: {}", status);
                fillMissingFields(candidate);
                return;
            }

            JsonNode messages = adk.getMessages(auth, threadId);
            String agentResponse = "";
            for (int i = messages.size() - 1; i >= 0; i--) {
                JsonNode msg = messages.get(i);
                if ("assistant".equals(msg.path("role").asText())) {
                    agentResponse = extractContent(msg);
                    break;
                }
            }

            boolean passed = applyAgentResponse(candidate, agentResponse);
            logger.info("<<< AI Pre-Screening for {}: {} (tag: {}, missing: {})",
                    candidate.getFullName(),
                    passed ? "PASSED" : "REJECTED",
                    candidate.getAiTag(),
                    candidate.getMissingFields());

        } catch (Exception e) {
            logger.error("Error calling wx.O Prescreen Agent: {}", e.getMessage());
            fillMissingFields(candidate);
        }
    }

    private String buildPrompt(Candidate candidate) {
        StringBuilder sb = new StringBuilder();
        sb.append("You are screening a candidate. The Application Agent has already extracted the ")
                .append("candidate's structured data from their CV. Your job is ONLY to:\n")
                .append("  A) Make a go/no-go decision (APPROVED or DENIED)\n")
                .append("  B) Assign a match tag\n")
                .append("  C) Identify which of the required fields are still missing or blank\n\n");

        sb.append("Candidate name: ").append(safe(candidate.getFirstName()))
                .append(' ').append(safe(candidate.getLastName())).append('\n');
        sb.append("Applied position: ").append(safe(candidate.getPosition())).append('\n');

        // Send the already-extracted structured fields so the agent can judge fit
        // and identify gaps — no re-extraction needed.
        sb.append("\n--- Already-extracted candidate fields ---\n");
        sb.append("EMAIL: ").append(safe(candidate.getEmail())).append('\n');
        sb.append("PHONE: ").append(safe(candidate.getPhone())).append('\n');
        sb.append("SKILLS: ").append(safe(candidate.getSkills())).append('\n');
        sb.append("EXPERIENCE: ").append(safe(candidate.getExperience())).append('\n');
        sb.append("EDUCATION: ").append(safe(candidate.getEducation())).append('\n');

        if (candidate.getCvText() != null && !candidate.getCvText().isBlank()) {
            sb.append("\n--- Full CV text (for fit assessment only) ---\n");
            sb.append(candidate.getCvText()).append('\n');
            sb.append("--- end of CV ---\n");
        }

        sb.append("\nReply using EXACTLY this plain-text template (one field per line).\n\n")
                .append("DECISION: APPROVED or DENIED\n")
                .append("TAG: <one of: 'Strong match', 'Partial match', or 'Weak match'>\n")
                .append("MISSING: <comma-separated names of the fields above that are blank or UNKNOWN, ")
                .append("or NONE if all fields are present>\n");
        return sb.toString();
    }

    /**
     * Parses the agent's slim response (DECISION / TAG / MISSING only) and mutates
     * the candidate. Structured fields (email, phone, etc.) are NOT overwritten —
     * they were already set by the Application Agent before the process started.
     */
    private boolean applyAgentResponse(Candidate candidate, String response) {
        Map<String, String> fields = parseFields(response);

        String decision = fields.getOrDefault("DECISION", "APPROVED").toUpperCase();
        boolean passed = decision.contains("APPROVED");

        candidate.setAiTag(valueOrNull(fields.get("TAG")));

        // Collect missing fields from the agent's MISSING line.
        List<String> missing = new ArrayList<>();
        String missingRaw = fields.get("MISSING");
        if (missingRaw != null && !missingRaw.isBlank() && !"NONE".equalsIgnoreCase(missingRaw.trim())) {
            for (String part : missingRaw.split(",")) {
                String trimmed = part.trim();
                if (!trimmed.isEmpty())
                    missing.add(trimmed);
            }
        }
        // Cross-check directly against the candidate object — no re-extraction needed.
        for (String key : REQUIRED_FIELDS) {
            String value = getField(candidate, key);
            if ((value == null || value.isBlank()) && !missing.contains(key)) {
                missing.add(key);
            }
        }
        candidate.setMissingFields(missing);

        return passed;
    }

    /** Returns the value of a required field directly from the candidate object. */
    private String getField(Candidate candidate, String fieldName) {
        switch (fieldName) {
            case "email":      return candidate.getEmail();
            case "phone":      return candidate.getPhone();
            case "skills":     return candidate.getSkills();
            case "experience": return candidate.getExperience();
            case "education":  return candidate.getEducation();
            default:           return null;
        }
    }

    /** Very tolerant KEY: value parser — one field per line. Keeps last occurrence. */
    private Map<String, String> parseFields(String response) {
        Map<String, String> out = new LinkedHashMap<>();
        if (response == null)
            return out;
        for (String rawLine : response.split("\\r?\\n")) {
            String line = rawLine.trim();
            int idx = line.indexOf(':');
            if (idx <= 0)
                continue;
            String key = line.substring(0, idx).trim().toUpperCase();
            String value = line.substring(idx + 1).trim();
            if (!key.isEmpty())
                out.put(key, value);
        }
        return out;
    }

    private String valueOrNull(String v) {
        if (v == null)
            return null;
        String t = v.trim();
        if (t.isEmpty() || "UNKNOWN".equalsIgnoreCase(t) || "NONE".equalsIgnoreCase(t))
            return null;
        return t;
    }

    private String safe(String s) {
        return s == null ? "" : s;
    }

    /** When the agent cannot be reached we still want HR to see what is missing. */
    private void fillMissingFields(Candidate candidate) {
        candidate.setMissingFields(REQUIRED_FIELDS.stream()
                .filter(f -> {
                    switch (f) {
                        case "email":
                            return candidate.getEmail() == null || candidate.getEmail().isBlank();
                        case "phone":
                            return candidate.getPhone() == null || candidate.getPhone().isBlank();
                        case "skills":
                            return candidate.getSkills() == null || candidate.getSkills().isBlank();
                        case "experience":
                            return candidate.getExperience() == null || candidate.getExperience().isBlank();
                        case "education":
                            return candidate.getEducation() == null || candidate.getEducation().isBlank();
                        default:
                            return false;
                    }
                })
                .collect(Collectors.toList()));
        if (candidate.getAiTag() == null || candidate.getAiTag().isBlank()) {
            candidate.setAiTag("AI Prescreen unavailable — HR review required");
        }
    }

    private String getToken() throws Exception {
        if (cachedToken != null)
            return cachedToken;

        // Get global token with configured wx.O Developer Edition credentials
        String globalToken = adk.getToken(adkUsername, adkPassword, null)
                .get("access_token").asText();

        // Find tenant by configured name
        JsonNode tenants = adk.getTenants("Bearer " + globalToken);
        String tenantId = null;
        for (JsonNode t : tenants) {
            if (adkTenantName.equals(t.path("name").asText())) {
                tenantId = t.get("id").asText();
                break;
            }
        }
        if (tenantId == null)
            throw new RuntimeException("Tenant '" + adkTenantName + "' not found");

        // Get tenant-scoped token
        cachedToken = adk.getToken(adkUsername, adkPassword, tenantId)
                .get("access_token").asText();
        return cachedToken;
    }

    private String getAgentId(String token) throws Exception {
        if (cachedAgentId != null)
            return cachedAgentId;

        JsonNode agents = adk.getAgents("Bearer " + token, "Prescreen_Agent", true);
        if (agents.isEmpty()) {
            throw new RuntimeException("Agent 'Prescreen_Agent' not found. Import it first.");
        }
        cachedAgentId = agents.get(0).get("id").asText();
        return cachedAgentId;
    }

    private String extractContent(JsonNode message) {
        JsonNode content = message.get("content");
        if (content == null)
            return "No response";
        if (content.isTextual())
            return content.asText();
        if (content.isArray()) {
            StringBuilder sb = new StringBuilder();
            for (JsonNode item : content) {
                if (item.has("text"))
                    sb.append(item.get("text").asText());
            }
            return sb.length() > 0 ? sb.toString() : content.toString();
        }
        return content.toString();
    }
}
