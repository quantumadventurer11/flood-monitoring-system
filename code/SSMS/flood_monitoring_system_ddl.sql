/* Flood Monitoring System (FMS) — MS SQL Server DDL (Fixed batching)
   - Single batch (NO GO inside TRY/CATCH)
   - dbo schema
   - Surrogate keys: IDENTITY
   - UTC timestamps: datetime2(3)
*/

/* Create + select the database */
IF DB_ID(N'FloodMonitoringSystem') IS NULL
BEGIN
    CREATE DATABASE FloodMonitoringSystem;
END
GO

USE FloodMonitoringSystem;
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRAN;

    /* =========================
       DROP (child -> parent)
       ========================= */

    IF OBJECT_ID('dbo.NOTIFICATION','U') IS NOT NULL DROP TABLE dbo.NOTIFICATION;
    IF OBJECT_ID('dbo.ALERT','U')        IS NOT NULL DROP TABLE dbo.ALERT;
    IF OBJECT_ID('dbo.ALERT_RULE','U')   IS NOT NULL DROP TABLE dbo.ALERT_RULE;
    IF OBJECT_ID('dbo.USER_AREA_SUBSCRIPTION','U') IS NOT NULL DROP TABLE dbo.USER_AREA_SUBSCRIPTION;

    IF OBJECT_ID('dbo.EVENT_IMPACT','U') IS NOT NULL DROP TABLE dbo.EVENT_IMPACT;
    IF OBJECT_ID('dbo.FLOOD_EVENT','U')  IS NOT NULL DROP TABLE dbo.FLOOD_EVENT;
    IF OBJECT_ID('dbo.MODEL_OUTPUT','U') IS NOT NULL DROP TABLE dbo.MODEL_OUTPUT;
    IF OBJECT_ID('dbo.MODEL_INPUT','U')  IS NOT NULL DROP TABLE dbo.MODEL_INPUT;
    IF OBJECT_ID('dbo.MODEL_RUN','U')    IS NOT NULL DROP TABLE dbo.MODEL_RUN;

    IF OBJECT_ID('dbo.INGEST_ERROR','U') IS NOT NULL DROP TABLE dbo.INGEST_ERROR;
    IF OBJECT_ID('dbo.INGEST_JOB','U')   IS NOT NULL DROP TABLE dbo.INGEST_JOB;
    IF OBJECT_ID('dbo.DATA_SOURCE','U')  IS NOT NULL DROP TABLE dbo.DATA_SOURCE;

    IF OBJECT_ID('dbo.MEASUREMENT','U')  IS NOT NULL DROP TABLE dbo.MEASUREMENT;
    IF OBJECT_ID('dbo.SENSOR','U')       IS NOT NULL DROP TABLE dbo.SENSOR;
    IF OBJECT_ID('dbo.SENSOR_TYPE','U')  IS NOT NULL DROP TABLE dbo.SENSOR_TYPE;

    IF OBJECT_ID('dbo.STATION','U')         IS NOT NULL DROP TABLE dbo.STATION;
    IF OBJECT_ID('dbo.GEOGRAPHIC_AREA','U') IS NOT NULL DROP TABLE dbo.GEOGRAPHIC_AREA;

    IF OBJECT_ID('dbo.AUDIT_LOG','U')    IS NOT NULL DROP TABLE dbo.AUDIT_LOG;
    IF OBJECT_ID('dbo.USER_SESSION','U') IS NOT NULL DROP TABLE dbo.USER_SESSION;
    IF OBJECT_ID('dbo.[USER]','U')       IS NOT NULL DROP TABLE dbo.[USER];
    IF OBJECT_ID('dbo.ROLE','U')         IS NOT NULL DROP TABLE dbo.ROLE;

    /* =========================
       1) ACCESS CONTROL & AUDIT
       ========================= */

    CREATE TABLE dbo.ROLE (
        RoleID           INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ROLE PRIMARY KEY,
        RoleName         NVARCHAR(50)      NOT NULL,
        RoleDescription  NVARCHAR(255)     NULL,
        CreatedAt        DATETIME2(3)      NOT NULL CONSTRAINT DF_ROLE_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT UQ_ROLE_RoleName UNIQUE (RoleName)
    );

    CREATE TABLE dbo.[USER] (
        UserID        INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_USER PRIMARY KEY,
        RoleID        INT               NOT NULL,
        Email         NVARCHAR(320)     NOT NULL,
        DisplayName   NVARCHAR(120)     NOT NULL,
        PasswordHash  VARBINARY(256)    NOT NULL,
        IsActive      BIT               NOT NULL CONSTRAINT DF_USER_IsActive DEFAULT (1),
        CreatedAt     DATETIME2(3)      NOT NULL CONSTRAINT DF_USER_CreatedAt DEFAULT (SYSUTCDATETIME()),
        LastLoginAt   DATETIME2(3)      NULL,
        CONSTRAINT UQ_USER_Email UNIQUE (Email),
        CONSTRAINT FK_USER_ROLE FOREIGN KEY (RoleID) REFERENCES dbo.ROLE(RoleID)
    );

    CREATE TABLE dbo.USER_SESSION (
        SessionID           INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_USER_SESSION PRIMARY KEY,
        UserID              INT               NOT NULL,
        RefreshTokenHash    VARBINARY(256)    NOT NULL,
        IssuedAt            DATETIME2(3)      NOT NULL CONSTRAINT DF_USER_SESSION_IssuedAt DEFAULT (SYSUTCDATETIME()),
        ExpiresAt           DATETIME2(3)      NOT NULL,
        RevokedAt           DATETIME2(3)      NULL,
        ClientIP            NVARCHAR(45)      NULL,
        UserAgent           NVARCHAR(256)     NULL,
        CONSTRAINT FK_USER_SESSION_USER FOREIGN KEY (UserID) REFERENCES dbo.[USER](UserID) ON DELETE CASCADE
    );

    CREATE TABLE dbo.AUDIT_LOG (
        AuditLogID     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_AUDIT_LOG PRIMARY KEY,
        UserID         INT               NOT NULL,
        ActionType     NVARCHAR(50)      NOT NULL,
        EntityType     NVARCHAR(50)      NOT NULL,
        EntityID       NVARCHAR(64)      NOT NULL,
        MetadataJson   NVARCHAR(MAX)     NULL,
        OccurredAt     DATETIME2(3)      NOT NULL CONSTRAINT DF_AUDIT_LOG_OccurredAt DEFAULT (SYSUTCDATETIME()),
        SourceIP       NVARCHAR(45)      NULL,
        CONSTRAINT FK_AUDIT_LOG_USER FOREIGN KEY (UserID) REFERENCES dbo.[USER](UserID),
        CONSTRAINT CK_AUDIT_LOG_MetadataJson_IsJson CHECK (MetadataJson IS NULL OR ISJSON(MetadataJson) = 1)
    );

    CREATE INDEX IX_USER_SESSION_UserID_ExpiresAt ON dbo.USER_SESSION (UserID, ExpiresAt);
    CREATE INDEX IX_AUDIT_LOG_UserID_OccurredAt   ON dbo.AUDIT_LOG (UserID, OccurredAt);

    /* =========================
       2) GEOSPATIAL & STATIONS
       ========================= */

    CREATE TABLE dbo.GEOGRAPHIC_AREA (
        AreaID       INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_GEOGRAPHIC_AREA PRIMARY KEY,
        AreaName     NVARCHAR(120)     NOT NULL,
        AreaType     NVARCHAR(50)      NOT NULL,
        GeometryWKT  NVARCHAR(MAX)     NULL,
        MinLat       DECIMAL(9,6)      NULL,
        MinLon       DECIMAL(9,6)      NULL,
        MaxLat       DECIMAL(9,6)      NULL,
        MaxLon       DECIMAL(9,6)      NULL,
        CreatedAt    DATETIME2(3)      NOT NULL CONSTRAINT DF_GEOGRAPHIC_AREA_CreatedAt DEFAULT (SYSUTCDATETIME())
    );

    CREATE TABLE dbo.STATION (
        StationID     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_STATION PRIMARY KEY,
        AreaID        INT               NOT NULL,
        StationCode   NVARCHAR(50)      NOT NULL,
        StationName   NVARCHAR(120)     NOT NULL,
        Latitude      DECIMAL(9,6)      NOT NULL,
        Longitude     DECIMAL(9,6)      NOT NULL,
        ElevationM    DECIMAL(10,2)     NULL,
        Status        NVARCHAR(30)      NOT NULL CONSTRAINT DF_STATION_Status DEFAULT (N'ACTIVE'),
        InstalledAt   DATETIME2(3)      NULL,
        CONSTRAINT UQ_STATION_StationCode UNIQUE (StationCode),
        CONSTRAINT FK_STATION_AREA FOREIGN KEY (AreaID) REFERENCES dbo.GEOGRAPHIC_AREA(AreaID)
    );

    CREATE INDEX IX_STATION_AreaID ON dbo.STATION (AreaID);

    /* =========================
       3) SENSORS & MEASUREMENTS
       ========================= */

    CREATE TABLE dbo.SENSOR_TYPE (
        SensorTypeID  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_SENSOR_TYPE PRIMARY KEY,
        TypeName      NVARCHAR(80)      NOT NULL,
        Unit          NVARCHAR(32)      NULL,
        Description   NVARCHAR(255)     NULL,
        CONSTRAINT UQ_SENSOR_TYPE_TypeName UNIQUE (TypeName)
    );

    CREATE TABLE dbo.SENSOR (
        SensorID           INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_SENSOR PRIMARY KEY,
        StationID          INT               NOT NULL,
        SensorTypeID       INT               NOT NULL,
        SerialNumber       NVARCHAR(80)      NULL,
        Status             NVARCHAR(30)      NOT NULL CONSTRAINT DF_SENSOR_Status DEFAULT (N'ACTIVE'),
        InstalledAt        DATETIME2(3)      NULL,
        LastCalibrationAt  DATETIME2(3)      NULL,
        CONSTRAINT FK_SENSOR_STATION     FOREIGN KEY (StationID)    REFERENCES dbo.STATION(StationID),
        CONSTRAINT FK_SENSOR_SENSOR_TYPE FOREIGN KEY (SensorTypeID) REFERENCES dbo.SENSOR_TYPE(SensorTypeID)
    );

    CREATE INDEX IX_SENSOR_StationID    ON dbo.SENSOR (StationID);
    CREATE INDEX IX_SENSOR_SensorTypeID ON dbo.SENSOR (SensorTypeID);

    CREATE TABLE dbo.MEASUREMENT (
        MeasurementID  BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_MEASUREMENT PRIMARY KEY,
        StationID      INT               NOT NULL,
        SensorID       INT               NOT NULL,
        ObservedAt     DATETIME2(3)      NOT NULL,
        Value          DECIMAL(18,6)     NOT NULL,
        Unit           NVARCHAR(32)      NULL,
        QualityFlag    NVARCHAR(20)      NULL,
        IngestedAt     DATETIME2(3)      NOT NULL CONSTRAINT DF_MEASUREMENT_IngestedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_MEASUREMENT_STATION FOREIGN KEY (StationID) REFERENCES dbo.STATION(StationID),
        CONSTRAINT FK_MEASUREMENT_SENSOR  FOREIGN KEY (SensorID)  REFERENCES dbo.SENSOR(SensorID)
    );

    CREATE INDEX IX_MEASUREMENT_Station_ObservedAt ON dbo.MEASUREMENT (StationID, ObservedAt DESC);
    CREATE INDEX IX_MEASUREMENT_Sensor_ObservedAt  ON dbo.MEASUREMENT (SensorID, ObservedAt DESC);

    /* =========================
       4) INGESTION
       ========================= */

    CREATE TABLE dbo.DATA_SOURCE (
        DataSourceID  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_DATA_SOURCE PRIMARY KEY,
        SourceName    NVARCHAR(120)     NOT NULL,
        SourceType    NVARCHAR(50)      NOT NULL,
        Provider      NVARCHAR(120)     NULL,
        Endpoint      NVARCHAR(500)     NULL,
        AuthMethod    NVARCHAR(50)      NULL,
        IsActive      BIT               NOT NULL CONSTRAINT DF_DATA_SOURCE_IsActive DEFAULT (1),
        CreatedAt     DATETIME2(3)      NOT NULL CONSTRAINT DF_DATA_SOURCE_CreatedAt DEFAULT (SYSUTCDATETIME())
    );

    CREATE TABLE dbo.INGEST_JOB (
        IngestJobID     INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_INGEST_JOB PRIMARY KEY,
        DataSourceID    INT               NOT NULL,
        JobType         NVARCHAR(50)      NOT NULL,
        Status          NVARCHAR(30)      NOT NULL,
        StartedAt       DATETIME2(3)      NOT NULL CONSTRAINT DF_INGEST_JOB_StartedAt DEFAULT (SYSUTCDATETIME()),
        CompletedAt     DATETIME2(3)      NULL,
        ParametersJson  NVARCHAR(MAX)     NULL,
        OutputLocation  NVARCHAR(500)     NULL,
        CONSTRAINT FK_INGEST_JOB_DATA_SOURCE FOREIGN KEY (DataSourceID) REFERENCES dbo.DATA_SOURCE(DataSourceID),
        CONSTRAINT CK_INGEST_JOB_ParametersJson_IsJson CHECK (ParametersJson IS NULL OR ISJSON(ParametersJson) = 1)
    );

    CREATE TABLE dbo.INGEST_ERROR (
        IngestErrorID  INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_INGEST_ERROR PRIMARY KEY,
        IngestJobID    INT               NOT NULL,
        ErrorCode      NVARCHAR(50)      NULL,
        ErrorMessage   NVARCHAR(4000)    NOT NULL,
        OccurredAt     DATETIME2(3)      NOT NULL CONSTRAINT DF_INGEST_ERROR_OccurredAt DEFAULT (SYSUTCDATETIME()),
        ContextJson    NVARCHAR(MAX)     NULL,
        CONSTRAINT FK_INGEST_ERROR_INGEST_JOB FOREIGN KEY (IngestJobID) REFERENCES dbo.INGEST_JOB(IngestJobID) ON DELETE CASCADE,
        CONSTRAINT CK_INGEST_ERROR_ContextJson_IsJson CHECK (ContextJson IS NULL OR ISJSON(ContextJson) = 1)
    );

    CREATE INDEX IX_INGEST_JOB_DataSource_Status ON dbo.INGEST_JOB (DataSourceID, Status, StartedAt DESC);
    CREATE INDEX IX_INGEST_ERROR_IngestJobID     ON dbo.INGEST_ERROR (IngestJobID, OccurredAt DESC);

    /* =========================
       5) MODELING & EVENTS
       ========================= */

    CREATE TABLE dbo.MODEL_RUN (
        ModelRunID       BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_MODEL_RUN PRIMARY KEY,
        ModelName        NVARCHAR(120)     NOT NULL,
        ModelVersion     NVARCHAR(50)      NOT NULL,
        RunStartedAt     DATETIME2(3)      NOT NULL CONSTRAINT DF_MODEL_RUN_RunStartedAt DEFAULT (SYSUTCDATETIME()),
        RunCompletedAt   DATETIME2(3)      NULL,
        Status           NVARCHAR(30)      NOT NULL,
        ParametersJson   NVARCHAR(MAX)     NULL,
        Notes            NVARCHAR(1000)    NULL,
        CONSTRAINT CK_MODEL_RUN_ParametersJson_IsJson CHECK (ParametersJson IS NULL OR ISJSON(ParametersJson) = 1)
    );

    CREATE TABLE dbo.MODEL_INPUT (
        ModelInputID       BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_MODEL_INPUT PRIMARY KEY,
        ModelRunID         BIGINT          NOT NULL,
        InputType          NVARCHAR(50)    NOT NULL,
        SourceRef          NVARCHAR(500)   NULL,
        TimeStart          DATETIME2(3)    NULL,
        TimeEnd            DATETIME2(3)    NULL,
        InputMetadataJson  NVARCHAR(MAX)   NULL,
        CONSTRAINT FK_MODEL_INPUT_MODEL_RUN FOREIGN KEY (ModelRunID) REFERENCES dbo.MODEL_RUN(ModelRunID) ON DELETE CASCADE,
        CONSTRAINT CK_MODEL_INPUT_Metadata_IsJson CHECK (InputMetadataJson IS NULL OR ISJSON(InputMetadataJson) = 1)
    );

    CREATE TABLE dbo.MODEL_OUTPUT (
        ModelOutputID        BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_MODEL_OUTPUT PRIMARY KEY,
        ModelRunID           BIGINT          NOT NULL,
        OutputType           NVARCHAR(50)    NOT NULL,
        OutputRef            NVARCHAR(500)   NULL,
        OutputMetadataJson   NVARCHAR(MAX)   NULL,
        ProducedAt           DATETIME2(3)    NOT NULL CONSTRAINT DF_MODEL_OUTPUT_ProducedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_MODEL_OUTPUT_MODEL_RUN FOREIGN KEY (ModelRunID) REFERENCES dbo.MODEL_RUN(ModelRunID) ON DELETE CASCADE,
        CONSTRAINT CK_MODEL_OUTPUT_Metadata_IsJson CHECK (OutputMetadataJson IS NULL OR ISJSON(OutputMetadataJson) = 1)
    );

    CREATE TABLE dbo.FLOOD_EVENT (
        FloodEventID  BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_FLOOD_EVENT PRIMARY KEY,
        ModelRunID    BIGINT          NOT NULL,
        AreaID        INT             NOT NULL,
        DetectedAt    DATETIME2(3)    NOT NULL CONSTRAINT DF_FLOOD_EVENT_DetectedAt DEFAULT (SYSUTCDATETIME()),
        EventStart    DATETIME2(3)    NULL,
        EventEnd      DATETIME2(3)    NULL,
        Confidence    NVARCHAR(30)    NULL,
        Summary       NVARCHAR(1000)  NULL,
        CONSTRAINT FK_FLOOD_EVENT_MODEL_RUN FOREIGN KEY (ModelRunID) REFERENCES dbo.MODEL_RUN(ModelRunID) ON DELETE CASCADE,
        CONSTRAINT FK_FLOOD_EVENT_AREA      FOREIGN KEY (AreaID)    REFERENCES dbo.GEOGRAPHIC_AREA(AreaID)
    );

    CREATE TABLE dbo.EVENT_IMPACT (
        ImpactID                 BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_EVENT_IMPACT PRIMARY KEY,
        FloodEventID             BIGINT          NOT NULL,
        ImpactType               NVARCHAR(50)    NOT NULL,
        Severity                 NVARCHAR(20)    NULL,
        EstimatedAreaSqKm        DECIMAL(12,2)   NULL,
        EstimatedPeopleAffected  INT             NULL,
        Notes                    NVARCHAR(1000)  NULL,
        CONSTRAINT FK_EVENT_IMPACT_FLOOD_EVENT FOREIGN KEY (FloodEventID) REFERENCES dbo.FLOOD_EVENT(FloodEventID) ON DELETE CASCADE
    );

    CREATE INDEX IX_MODEL_INPUT_ModelRunID            ON dbo.MODEL_INPUT (ModelRunID);
    CREATE INDEX IX_MODEL_OUTPUT_ModelRunID_ProducedAt ON dbo.MODEL_OUTPUT (ModelRunID, ProducedAt DESC);
    CREATE INDEX IX_FLOOD_EVENT_Area_DetectedAt       ON dbo.FLOOD_EVENT (AreaID, DetectedAt DESC);

    /* =========================
       6) ALERTING & NOTIFICATIONS
       ========================= */

    CREATE TABLE dbo.USER_AREA_SUBSCRIPTION (
        SubscriptionID   INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_USER_AREA_SUBSCRIPTION PRIMARY KEY,
        UserID           INT               NOT NULL,
        AreaID           INT               NOT NULL,
        PreferenceJson   NVARCHAR(MAX)     NULL,
        IsActive         BIT               NOT NULL CONSTRAINT DF_USER_AREA_SUBSCRIPTION_IsActive DEFAULT (1),
        CreatedAt        DATETIME2(3)      NOT NULL CONSTRAINT DF_USER_AREA_SUBSCRIPTION_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_USER_AREA_SUBSCRIPTION_USER FOREIGN KEY (UserID) REFERENCES dbo.[USER](UserID) ON DELETE CASCADE,
        CONSTRAINT FK_USER_AREA_SUBSCRIPTION_AREA FOREIGN KEY (AreaID) REFERENCES dbo.GEOGRAPHIC_AREA(AreaID),
        CONSTRAINT UQ_USER_AREA_SUBSCRIPTION_User_Area UNIQUE (UserID, AreaID),
        CONSTRAINT CK_USER_AREA_SUBSCRIPTION_Preference_IsJson CHECK (PreferenceJson IS NULL OR ISJSON(PreferenceJson) = 1)
    );

    CREATE TABLE dbo.ALERT_RULE (
        AlertRuleID      INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ALERT_RULE PRIMARY KEY,
        StationID        INT               NOT NULL,
        AreaID           INT               NOT NULL,
        RuleName         NVARCHAR(120)     NOT NULL,
        Metric           NVARCHAR(80)      NOT NULL,
        Operator         NVARCHAR(10)      NOT NULL,
        ThresholdValue   DECIMAL(18,6)     NOT NULL,
        WindowMinutes    INT               NOT NULL,
        Severity         NVARCHAR(20)      NOT NULL,
        IsEnabled        BIT               NOT NULL CONSTRAINT DF_ALERT_RULE_IsEnabled DEFAULT (1),
        CreatedAt        DATETIME2(3)      NOT NULL CONSTRAINT DF_ALERT_RULE_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_ALERT_RULE_STATION FOREIGN KEY (StationID) REFERENCES dbo.STATION(StationID),
        CONSTRAINT FK_ALERT_RULE_AREA    FOREIGN KEY (AreaID)    REFERENCES dbo.GEOGRAPHIC_AREA(AreaID),
        CONSTRAINT CK_ALERT_RULE_WindowMinutes CHECK (WindowMinutes > 0),
        CONSTRAINT CK_ALERT_RULE_Operator CHECK (Operator IN (N'>', N'>=', N'<', N'<=', N'=', N'!='))
    );

    CREATE TABLE dbo.ALERT (
        AlertID          BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ALERT PRIMARY KEY,
        AlertRuleID      INT               NOT NULL,
        StationID        INT               NOT NULL,
        UserID           INT               NOT NULL,
        TriggeredAt      DATETIME2(3)      NOT NULL CONSTRAINT DF_ALERT_TriggeredAt DEFAULT (SYSUTCDATETIME()),
        Severity         NVARCHAR(20)      NOT NULL,
        Status           NVARCHAR(30)      NOT NULL,
        Summary          NVARCHAR(1000)    NULL,
        DetailsJson      NVARCHAR(MAX)     NULL,
        AcknowledgedAt   DATETIME2(3)      NULL,
        CONSTRAINT FK_ALERT_ALERT_RULE FOREIGN KEY (AlertRuleID) REFERENCES dbo.ALERT_RULE(AlertRuleID),
        CONSTRAINT FK_ALERT_STATION    FOREIGN KEY (StationID)   REFERENCES dbo.STATION(StationID),
        CONSTRAINT FK_ALERT_USER       FOREIGN KEY (UserID)      REFERENCES dbo.[USER](UserID),
        CONSTRAINT CK_ALERT_Details_IsJson CHECK (DetailsJson IS NULL OR ISJSON(DetailsJson) = 1)
    );

    CREATE TABLE dbo.NOTIFICATION (
        NotificationID      BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_NOTIFICATION PRIMARY KEY,
        AlertID             BIGINT           NOT NULL,
        UserID              INT              NOT NULL,
        Channel             NVARCHAR(20)     NOT NULL,
        Destination         NVARCHAR(256)    NOT NULL,
        Status              NVARCHAR(30)     NOT NULL,
        QueuedAt            DATETIME2(3)     NOT NULL CONSTRAINT DF_NOTIFICATION_QueuedAt DEFAULT (SYSUTCDATETIME()),
        SentAt              DATETIME2(3)     NULL,
        ProviderMessageID   NVARCHAR(128)    NULL,
        CONSTRAINT FK_NOTIFICATION_ALERT FOREIGN KEY (AlertID) REFERENCES dbo.ALERT(AlertID) ON DELETE CASCADE,
        CONSTRAINT FK_NOTIFICATION_USER  FOREIGN KEY (UserID)  REFERENCES dbo.[USER](UserID)
    );

    CREATE INDEX IX_ALERT_RULE_Station_Enabled ON dbo.ALERT_RULE (StationID, IsEnabled);
    CREATE INDEX IX_ALERT_Station_TriggeredAt  ON dbo.ALERT (StationID, TriggeredAt DESC);
    CREATE INDEX IX_ALERT_Status_TriggeredAt   ON dbo.ALERT (Status, TriggeredAt DESC);
    CREATE INDEX IX_NOTIFICATION_User_Status   ON dbo.NOTIFICATION (UserID, Status, QueuedAt DESC);

    COMMIT TRAN;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRAN;
    THROW;
END CATCH;



-- Enforce redundancy safely -- 
-- This is to be executed after the DDL.

USE FloodMonitoringSystem;
GO

/* 1) ALERT_RULE must be unique by (AlertRuleID, StationID) so ALERT can reference both */
IF NOT EXISTS (
  SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_ALERT_RULE_AlertRuleID_StationID'
)
BEGIN
  ALTER TABLE dbo.ALERT_RULE
  ADD CONSTRAINT UQ_ALERT_RULE_AlertRuleID_StationID UNIQUE (AlertRuleID, StationID);
END
GO

/* 2) SENSOR must be unique by (SensorID, StationID) so MEASUREMENT can reference both */
IF NOT EXISTS (
  SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_SENSOR_SensorID_StationID'
)
BEGIN
  ALTER TABLE dbo.SENSOR
  ADD CONSTRAINT UQ_SENSOR_SensorID_StationID UNIQUE (SensorID, StationID);
END
GO

/* 3) Replace ALERT’s single-column FK to ALERT_RULE with composite FK enforcing station match */
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_ALERT_ALERT_RULE')
BEGIN
  ALTER TABLE dbo.ALERT DROP CONSTRAINT FK_ALERT_ALERT_RULE;
END
GO

ALTER TABLE dbo.ALERT
ADD CONSTRAINT FK_ALERT_ALERT_RULE_STATION
FOREIGN KEY (AlertRuleID, StationID)
REFERENCES dbo.ALERT_RULE (AlertRuleID, StationID);
GO

/* 4) Replace MEASUREMENT’s single-column FK to SENSOR with composite FK enforcing station match */
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_MEASUREMENT_SENSOR')
BEGIN
  ALTER TABLE dbo.MEASUREMENT DROP CONSTRAINT FK_MEASUREMENT_SENSOR;
END
GO

ALTER TABLE dbo.MEASUREMENT
ADD CONSTRAINT FK_MEASUREMENT_SENSOR_STATION
FOREIGN KEY (SensorID, StationID)
REFERENCES dbo.SENSOR (SensorID, StationID);
GO

USE FloodMonitoringSystem;
GO

-- Optional cleanup: remove redundant FKs after composite enforcement (recommended for clean documentation)

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_ALERT_STATION')
BEGIN
    ALTER TABLE dbo.ALERT DROP CONSTRAINT FK_ALERT_STATION;
END
GO

-- Keeping FK_MEASUREMENT_STATION is optional.
-- If you want maximum normalization + no duplicate dictionary rows, drop it too:

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_MEASUREMENT_STATION')
BEGIN
    ALTER TABLE dbo.MEASUREMENT DROP CONSTRAINT FK_MEASUREMENT_STATION;
END
GO

-- Add check constraints

USE FloodMonitoringSystem;
GO

/* ALERT_RULE.Operator */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_ALERT_RULE_Operator')
BEGIN
  ALTER TABLE dbo.ALERT_RULE
  ADD CONSTRAINT CK_ALERT_RULE_Operator
  CHECK (Operator IN (N'>', N'>=', N'<', N'<=', N'=', N'!='));
END
GO

/* ALERT_RULE.WindowMinutes */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_ALERT_RULE_WindowMinutes')
BEGIN
  ALTER TABLE dbo.ALERT_RULE
  ADD CONSTRAINT CK_ALERT_RULE_WindowMinutes
  CHECK (WindowMinutes > 0);
END
GO

/* Severity standardization (ALERT_RULE + ALERT + EVENT_IMPACT optional) */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_ALERT_RULE_Severity')
BEGIN
  ALTER TABLE dbo.ALERT_RULE
  ADD CONSTRAINT CK_ALERT_RULE_Severity
  CHECK (Severity IN (N'LOW', N'MEDIUM', N'HIGH', N'CRITICAL'));
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_ALERT_Severity')
BEGIN
  ALTER TABLE dbo.ALERT
  ADD CONSTRAINT CK_ALERT_Severity
  CHECK (Severity IN (N'LOW', N'MEDIUM', N'HIGH', N'CRITICAL'));
END
GO

/* ALERT.Status */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_ALERT_Status')
BEGIN
  ALTER TABLE dbo.ALERT
  ADD CONSTRAINT CK_ALERT_Status
  CHECK (Status IN (N'TRIGGERED', N'ACKNOWLEDGED', N'RESOLVED', N'FALSE_POSITIVE'));
END
GO

/* NOTIFICATION.Channel + Status */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_NOTIFICATION_Channel')
BEGIN
  ALTER TABLE dbo.NOTIFICATION
  ADD CONSTRAINT CK_NOTIFICATION_Channel
  CHECK (Channel IN (N'EMAIL', N'SMS', N'PUSH', N'WEBHOOK'));
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = 'CK_NOTIFICATION_Status')
BEGIN
  ALTER TABLE dbo.NOTIFICATION
  ADD CONSTRAINT CK_NOTIFICATION_Status
  CHECK (Status IN (N'QUEUED', N'SENT', N'FAILED'));
END
GO
