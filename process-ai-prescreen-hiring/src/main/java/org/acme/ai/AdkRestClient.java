package org.acme.ai;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.FormParam;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@RegisterRestClient(configKey = "adk")
@Path("")
@Produces(MediaType.APPLICATION_JSON)
public interface AdkRestClient {

    @POST
    @Path("/api/v1/auth/token")
    @Consumes(MediaType.APPLICATION_FORM_URLENCODED)
    JsonNode getToken(@FormParam("username") String username,
            @FormParam("password") String password,
            @QueryParam("tenant_id") String tenantId);

    @GET
    @Path("/api/v1/tenants")
    JsonNode getTenants(@HeaderParam("Authorization") String auth);

    @GET
    @Path("/v1/orchestrate/agents")
    JsonNode getAgents(@HeaderParam("Authorization") String auth,
            @QueryParam("names") String names,
            @QueryParam("include_hidden") boolean includeHidden);

    @POST
    @Path("/v1/orchestrate/runs")
    @Consumes(MediaType.APPLICATION_JSON)
    JsonNode createRun(@HeaderParam("Authorization") String auth, JsonNode body);

    @GET
    @Path("/v1/orchestrate/runs/{runId}")
    JsonNode getRunStatus(@HeaderParam("Authorization") String auth,
            @PathParam("runId") String runId);

    @GET
    @Path("/v1/threads/{threadId}/messages")
    JsonNode getMessages(@HeaderParam("Authorization") String auth,
            @PathParam("threadId") String threadId);
}
