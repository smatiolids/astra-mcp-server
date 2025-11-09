from astrapy.constants import SortMode
from astrapy.info import (
    CreateTableDefinition,
    ColumnType,
    TableScalarColumnTypeDescriptor,
    TableValuedColumnTypeDescriptor,
    TableValuedColumnType,
    TablePrimaryKeyDescriptor,
)


audit_table_definition = CreateTableDefinition(
    columns={
        "tool_id": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "date": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "run_id": TableScalarColumnTypeDescriptor(column_type=ColumnType.UUID),
        "client_id": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "start_timestamp": TableScalarColumnTypeDescriptor(column_type=ColumnType.TIMESTAMP),
        "end_timestamp": TableScalarColumnTypeDescriptor(column_type=ColumnType.TIMESTAMP),
        "keys": TableValuedColumnTypeDescriptor(
            column_type=TableValuedColumnType.SET,
            value_type=ColumnType.TEXT,
        ),
        "parameters": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "result": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "error": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "status": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "status_code": TableScalarColumnTypeDescriptor(column_type=ColumnType.INT),
        "status_message": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
        "status_details": TableScalarColumnTypeDescriptor(column_type=ColumnType.TEXT),
    },
    primary_key=TablePrimaryKeyDescriptor(partition_by=["tool_id", "date"], 
                                          partition_sort={"run_id": SortMode.DESCENDING}),
)