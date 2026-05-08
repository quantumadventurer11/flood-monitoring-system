USE FloodMonitoringSystem;
GO

SET NOCOUNT ON;

PRINT '=====================================================';
PRINT 'DATA DICTIONARY EXTRACTION';
PRINT 'Database: ' + DB_NAME();
PRINT '=====================================================';


/* ======================================================
   1. COLUMN STRUCTURE
   ====================================================== */

PRINT 'SECTION 1: COLUMN STRUCTURE';
PRINT '-----------------------------------------------------';

SELECT
    t.name AS TableName,
    c.column_id AS Ordinal,
    c.name AS ColumnName,
    ty.name AS DataType,
    CASE
        WHEN ty.name IN ('nvarchar','nchar','varchar','char','varbinary','binary')
            THEN '(' + 
                 CASE 
                    WHEN c.max_length = -1 THEN 'MAX'
                    WHEN ty.name LIKE 'n%' THEN CAST(c.max_length/2 AS VARCHAR(10))
                    ELSE CAST(c.max_length AS VARCHAR(10))
                 END + ')'
        WHEN ty.name IN ('decimal','numeric')
            THEN '(' + CAST(c.precision AS VARCHAR(10)) + ',' + CAST(c.scale AS VARCHAR(10)) + ')'
        ELSE ''
    END AS DataTypeDetail,
    CASE WHEN c.is_nullable = 1 THEN 'Y' ELSE 'N' END AS Nullable,
    CASE WHEN pk.column_id IS NOT NULL THEN 'PK' ELSE '' END AS IsPrimaryKey,
    dc.name AS DefaultConstraint,
    dc.definition AS DefaultDefinition
FROM sys.tables t
JOIN sys.columns c ON t.object_id = c.object_id
JOIN sys.types ty ON c.user_type_id = ty.user_type_id
LEFT JOIN (
    SELECT ic.object_id, ic.column_id
    FROM sys.indexes i
    JOIN sys.index_columns ic 
        ON i.object_id = ic.object_id 
        AND i.index_id = ic.index_id
    WHERE i.is_primary_key = 1
) pk ON pk.object_id = c.object_id AND pk.column_id = c.column_id
LEFT JOIN sys.default_constraints dc 
    ON dc.parent_object_id = c.object_id
   AND dc.parent_column_id = c.column_id
ORDER BY t.name, c.column_id;

PRINT '=====================================================';


/* ======================================================
   2. PRIMARY KEYS (GROUPED)
   ====================================================== */

PRINT 'SECTION 2: PRIMARY KEYS';
PRINT '-----------------------------------------------------';

SELECT
    t.name AS TableName,
    i.name AS PKName,
    STRING_AGG(c.name, ', ') 
        WITHIN GROUP (ORDER BY ic.key_ordinal) AS Columns
FROM sys.indexes i
JOIN sys.index_columns ic 
    ON i.object_id = ic.object_id 
    AND i.index_id = ic.index_id
JOIN sys.columns c 
    ON c.object_id = ic.object_id 
    AND c.column_id = ic.column_id
JOIN sys.tables t 
    ON t.object_id = i.object_id
WHERE i.is_primary_key = 1
GROUP BY t.name, i.name
ORDER BY t.name;

PRINT '=====================================================';


/* ======================================================
   3. FOREIGN KEYS (GROUPED – COMPOSITE SAFE)
   ====================================================== */

PRINT 'SECTION 3: FOREIGN KEYS';
PRINT '-----------------------------------------------------';

SELECT
    fk.name AS FKName,
    pt.name AS ParentTable,
    STRING_AGG(pc.name, ', ') 
        WITHIN GROUP (ORDER BY fkc.constraint_column_id) AS ParentColumns,
    rt.name AS ReferencedTable,
    STRING_AGG(rc.name, ', ') 
        WITHIN GROUP (ORDER BY fkc.constraint_column_id) AS ReferencedColumns,
    fk.delete_referential_action_desc AS OnDelete,
    fk.update_referential_action_desc AS OnUpdate
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc 
    ON fk.object_id = fkc.constraint_object_id
JOIN sys.tables pt 
    ON pt.object_id = fk.parent_object_id
JOIN sys.columns pc 
    ON pc.object_id = pt.object_id 
    AND pc.column_id = fkc.parent_column_id
JOIN sys.tables rt 
    ON rt.object_id = fk.referenced_object_id
JOIN sys.columns rc 
    ON rc.object_id = rt.object_id 
    AND rc.column_id = fkc.referenced_column_id
GROUP BY 
    fk.name,
    pt.name,
    rt.name,
    fk.delete_referential_action_desc,
    fk.update_referential_action_desc
ORDER BY pt.name, fk.name;

PRINT '=====================================================';


/* ======================================================
   4. UNIQUE CONSTRAINTS
   ====================================================== */

PRINT 'SECTION 4: UNIQUE CONSTRAINTS';
PRINT '-----------------------------------------------------';

SELECT
    t.name AS TableName,
    kc.name AS ConstraintName,
    STRING_AGG(c.name, ', ') 
        WITHIN GROUP (ORDER BY ic.key_ordinal) AS Columns
FROM sys.key_constraints kc
JOIN sys.tables t 
    ON t.object_id = kc.parent_object_id
JOIN sys.index_columns ic 
    ON ic.object_id = kc.parent_object_id 
    AND ic.index_id = kc.unique_index_id
JOIN sys.columns c 
    ON c.object_id = ic.object_id 
    AND c.column_id = ic.column_id
WHERE kc.type = 'UQ'
GROUP BY t.name, kc.name
ORDER BY t.name;

PRINT '=====================================================';


/* ======================================================
   5. CHECK CONSTRAINTS
   ====================================================== */

PRINT 'SECTION 5: CHECK CONSTRAINTS';
PRINT '-----------------------------------------------------';

SELECT
    OBJECT_NAME(parent_object_id) AS TableName,
    name AS CheckName,
    definition AS CheckDefinition
FROM sys.check_constraints
ORDER BY TableName, CheckName;

PRINT '=====================================================';
PRINT 'DATA DICTIONARY EXTRACTION COMPLETE';
PRINT '=====================================================';