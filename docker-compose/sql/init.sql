-- Licensed to the Apache Software Foundation (ASF) under one
-- or more contributor license agreements.  See the NOTICE file
-- distributed with this work for additional information
-- regarding copyright ownership.  The ASF licenses this file
-- to you under the Apache License, Version 2.0 (the
-- "License"); you may not use this file except in compliance
-- with the License.  You may obtain a copy of the License at
--
--  http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing,
-- software distributed under the License is distributed on an
-- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
-- KIND, either express or implied.  See the License for the
-- specific language governing permissions and limitations
-- under the License.

-- NOTE: 'kie-pass' is a demo-only password for LOCAL Docker development only.
-- It is intentionally simple so the demo works out of the box.
-- CHANGE this before any non-local, shared, or internet-facing deployment:
--   1. Update KIE_DB_PASSWORD in your .env file.
--   2. Replace 'kie-pass' with the same new value in this script.
-- This script runs only on first container startup (PostgreSQL initdb).
CREATE ROLE "kie-user" WITH
    LOGIN
    SUPERUSER
    INHERIT
    CREATEDB
    CREATEROLE
    NOREPLICATION
    PASSWORD 'kie-pass';

CREATE DATABASE kie
    WITH
    OWNER = "kie-user"
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

CREATE DATABASE kie_ai
    WITH
    OWNER = "kie-user"
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

GRANT ALL PRIVILEGES ON DATABASE postgres TO "kie-user";
GRANT ALL PRIVILEGES ON DATABASE kie TO "kie-user";
GRANT ALL PRIVILEGES ON DATABASE kie TO postgres;
GRANT ALL PRIVILEGES ON DATABASE kie_ai TO "kie-user";
GRANT ALL PRIVILEGES ON DATABASE kie_ai TO postgres;