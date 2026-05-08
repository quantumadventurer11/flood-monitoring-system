USE FloodMonitoringSystem;
GO

SET NOCOUNT ON;

-- Clean out data so the test can be rerun without UNIQUE constraint failures
DELETE FROM dbo.NOTIFICATION;
DELETE FROM dbo.ALERT;
DELETE FROM dbo.ALERT_RULE;
DELETE FROM dbo.USER_AREA_SUBSCRIPTION;

DELETE FROM dbo.EVENT_IMPACT;
DELETE FROM dbo.FLOOD_EVENT;
DELETE FROM dbo.MODEL_OUTPUT;
DELETE FROM dbo.MODEL_INPUT;
DELETE FROM dbo.MODEL_RUN;

DELETE FROM dbo.INGEST_ERROR;
DELETE FROM dbo.INGEST_JOB;
DELETE FROM dbo.DATA_SOURCE;

DELETE FROM dbo.MEASUREMENT;
DELETE FROM dbo.SENSOR;
DELETE FROM dbo.SENSOR_TYPE;

DELETE FROM dbo.STATION;
DELETE FROM dbo.GEOGRAPHIC_AREA;

DELETE FROM dbo.AUDIT_LOG;
DELETE FROM dbo.USER_SESSION;
DELETE FROM dbo.[USER];
DELETE FROM dbo.ROLE;

-- Insert seed data

INSERT INTO dbo.ROLE (RoleName, RoleDescription)
VALUES (N'Admin', N'Full access'), (N'Analyst', N'Analysis access');

INSERT INTO dbo.[USER] (RoleID, Email, DisplayName, PasswordHash)
SELECT RoleID, N'benjamin@example.com', N'Benjamin',
       CONVERT(varbinary(256), HASHBYTES('SHA2_256', 'ChangeMe123!'))
FROM dbo.ROLE
WHERE RoleName = N'Admin';

INSERT INTO dbo.GEOGRAPHIC_AREA (AreaName, AreaType, MinLat, MinLon, MaxLat, MaxLon)
VALUES (N'Dartmouth Test Area', N'CITY', 44.60, -63.65, 44.75, -63.45);

INSERT INTO dbo.STATION (AreaID, StationCode, StationName, Latitude, Longitude, ElevationM)
SELECT AreaID, N'STN-001', N'Test Station 001', 44.67, -63.57, 10.0
FROM dbo.GEOGRAPHIC_AREA
WHERE AreaName = N'Dartmouth Test Area';

INSERT INTO dbo.SENSOR_TYPE (TypeName, Unit, Description)
VALUES (N'WaterLevel', N'm', N'River or gauge water level');

INSERT INTO dbo.SENSOR (StationID, SensorTypeID, SerialNumber)
SELECT s.StationID, st.SensorTypeID, N'SN-TEST-001'
FROM dbo.STATION s
JOIN dbo.SENSOR_TYPE st ON st.TypeName = N'WaterLevel'
WHERE s.StationCode = N'STN-001';

INSERT INTO dbo.MEASUREMENT (StationID, SensorID, ObservedAt, Value, Unit, QualityFlag)
SELECT s.StationID, se.SensorID, SYSUTCDATETIME(), 1.234567, N'm', N'GOOD'
FROM dbo.STATION s
JOIN dbo.SENSOR se ON se.StationID = s.StationID
WHERE s.StationCode = N'STN-001';

INSERT INTO dbo.ALERT_RULE (StationID, AreaID, RuleName, Metric, Operator, ThresholdValue, WindowMinutes, Severity)
SELECT s.StationID, s.AreaID, N'Water Level High', N'WaterLevel', N'>=', 1.20, 15, N'HIGH'
FROM dbo.STATION s
WHERE s.StationCode = N'STN-001';

INSERT INTO dbo.ALERT (AlertRuleID, StationID, UserID, Severity, Status, Summary)
SELECT ar.AlertRuleID, ar.StationID, u.UserID, ar.Severity, N'TRIGGERED', N'Test alert fired'
FROM dbo.ALERT_RULE ar
JOIN dbo.[USER] u ON u.Email = N'benjamin@example.com'
WHERE ar.RuleName = N'Water Level High';

INSERT INTO dbo.NOTIFICATION (AlertID, UserID, Channel, Destination, Status)
SELECT a.AlertID, a.UserID, N'EMAIL', N'benjamin@example.com', N'QUEUED'
FROM dbo.ALERT a
WHERE a.Summary = N'Test alert fired';

-- A) Station → Sensor → Measurement
SELECT
  s.StationCode,
  s.StationName,
  st.TypeName AS SensorType,
  m.ObservedAt,
  m.Value,
  m.Unit,
  m.QualityFlag
FROM dbo.MEASUREMENT m
JOIN dbo.SENSOR se ON se.SensorID = m.SensorID
JOIN dbo.SENSOR_TYPE st ON st.SensorTypeID = se.SensorTypeID
JOIN dbo.STATION s ON s.StationID = m.StationID
ORDER BY m.ObservedAt DESC;

-- B) AlertRule → Alert → Notification
SELECT
  ar.RuleName,
  a.TriggeredAt,
  a.Severity,
  a.Status,
  n.Channel,
  n.Destination,
  n.Status AS NotificationStatus,
  n.QueuedAt,
  n.SentAt
FROM dbo.ALERT a
JOIN dbo.ALERT_RULE ar ON ar.AlertRuleID = a.AlertRuleID
LEFT JOIN dbo.NOTIFICATION n ON n.AlertID = a.AlertID
ORDER BY a.TriggeredAt DESC;

-- C) ModelRun → FloodEvent → EventImpact
INSERT INTO dbo.MODEL_RUN (ModelName, ModelVersion, Status)
VALUES (N'FloodClassifier', N'1.0', N'COMPLETED');

DECLARE @runId BIGINT = SCOPE_IDENTITY();

INSERT INTO dbo.FLOOD_EVENT (ModelRunID, AreaID, Confidence, Summary)
SELECT @runId, AreaID, N'HIGH', N'Test flood event'
FROM dbo.GEOGRAPHIC_AREA
WHERE AreaName = N'Dartmouth Test Area';

DECLARE @eventId BIGINT = SCOPE_IDENTITY();

INSERT INTO dbo.EVENT_IMPACT (FloodEventID, ImpactType, Severity, EstimatedAreaSqKm, EstimatedPeopleAffected)
VALUES (@eventId, N'Inundation', N'MEDIUM', 2.50, 1200);

SELECT
  mr.ModelName,
  mr.ModelVersion,
  fe.DetectedAt,
  ga.AreaName,
  fe.Confidence,
  ei.ImpactType,
  ei.Severity,
  ei.EstimatedAreaSqKm,
  ei.EstimatedPeopleAffected
FROM dbo.FLOOD_EVENT fe
JOIN dbo.MODEL_RUN mr ON mr.ModelRunID = fe.ModelRunID
JOIN dbo.GEOGRAPHIC_AREA ga ON ga.AreaID = fe.AreaID
LEFT JOIN dbo.EVENT_IMPACT ei ON ei.FloodEventID = fe.FloodEventID
ORDER BY fe.DetectedAt DESC;