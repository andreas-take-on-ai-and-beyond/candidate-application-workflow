// Copyright IBM Corp. 2025.
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

package org.acme.candidate;

import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties; // 1. DIESEN IMPORT HINZUFÜGEN
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true) // 2. DIESE ZEILE HINZUFÜGEN
public class Candidate {

    private String firstName;
    private String lastName;
    private String position;

    // Fields extracted by AI (Document Processing for wx.O) from the CV/resume.
    private String email;
    private String phone;
    private String skills;
    private String experience;
    private String education;

    // Raw CV text — accepted on input for AI prescreen, but never exposed in API output.
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String cvText;

    // AI-screening output: a short tag summarising the candidate (e.g. "Strong match — Senior Dev").
    private String aiTag;

    // Fields that the AI could not extract and which HR should ask the applicant for.
    private List<String> missingFields = new ArrayList<>();

    // --- NEU: DIESES FELD HINZUFÜGEN ---
    // Damit existiert die Eigenschaft physisch in der Klasse.
    private boolean cvAttached;

    public Candidate() {
    }

    public Candidate(String firstName, String lastName, String position) {
        this.firstName = firstName;
        this.lastName = lastName;
        this.position = position;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getPosition() {
        return position;
    }

    public void setPosition(String position) {
        this.position = position;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getSkills() {
        return skills;
    }

    public void setSkills(String skills) {
        this.skills = skills;
    }

    public String getExperience() {
        return experience;
    }

    public void setExperience(String experience) {
        this.experience = experience;
    }

    public String getEducation() {
        return education;
    }

    public void setEducation(String education) {
        this.education = education;
    }

    public String getCvText() {
        return cvText;
    }

    public void setCvText(String cvText) {
        this.cvText = cvText;
    }

    /*
     * ALT
     * public boolean isCvAttached() {
     * return cvText != null && !cvText.isBlank();
     * }
     */

    //NEU --- START
    // Wir ersetzen die alte isCvAttached Methode oder passen sie an:
    public boolean isCvAttached() {
        // Falls cvText vorhanden ist (Input), ist es true. 
        // Falls nicht, nehmen wir den Wert des Feldes.
        if (cvText != null && !cvText.isBlank()) {
            return true;
        }
        return cvAttached;
    }

    // Ganz wichtig: Der Marshaller braucht diesen Setter!
    public void setCvAttached(boolean cvAttached) {
        this.cvAttached = cvAttached;
    }
    //NEU --- ENDE

    public String getAiTag() {
        return aiTag;
    }

    public void setAiTag(String aiTag) {
        this.aiTag = aiTag;
    }

    public List<String> getMissingFields() {
        return missingFields;
    }

    public void setMissingFields(List<String> missingFields) {
        this.missingFields = missingFields == null ? new ArrayList<>() : missingFields;
    }

    @JsonIgnore
    public String getFullName() {
        return firstName + " " + lastName;
    }
}
