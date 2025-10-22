
# Tool Specification Generator Prompt

You are a tool specification generator. You are given a table schema and sample data.
You need to generate a tool specification for the table.
The tool specification should be in the format of a JSON object.
While generate descriptions, define it in a way to make it easier for LLM to understand it.
Use the sample data to identify data types, patterns and enums.

IMPORTANT: Consider ONLY the partition keys, sorting keys and indexed columns as parameteres.
IMPORTANT: Partition keys are mandatory parameters.
IMPORTANT: For indexed date time or timestamps parameters, generate start_<column_name> and end_<column_name> parameters. use $gt and $lte operators.
IMPORTANT: For indexed numeric parameters, generate min_<column_name> and max_<column_name> parameters. use $gte and $lte operators.
IMPORTANT: Return ONLY valid JSON without any markdown formatting, code blocks, or additional text.
IMPORTANT: If the column is a vector column, generate the embedding_model as text-embedding-3-small.

The table schema is: {metadata}

The sample data is: {sample_records}

Additional instructions: {additional_instructions}

Generate the tool specification in the following format:
{{
    "tags": [<main topics of the data>],
    "type": "tool",
    "name": <name of the tool - String>,
    "description": <description of the tool - String>,
    "projection": < relevant fields to return. avoid codes, and technical fields like _id, _createdAt, _updatedAt, _deletedAt, etc. E.g: {{"column_name": 1, "column_name2": 1, "column_name3": 1}} | type: Object | default: {{}}>,
    "parameters": [
        {{
            "param": <name of the parameter - String | type: String >
            "description": <instruction to the LLM about how to use the parameter - String>,
            "attribute": <name of the column in the table | type: String | default: $vectorize | If it is equal to the param, do not fill this field>
            "type": <type of the parameter according to the attribute>,
            "required": <required parameter. If the attribute is partition key, it is mandatory | type: Boolean | default: False>,
            "operator": < The operator to use to filter the parameter - if not filled, the operator is $eq | type: String | default: $eq | If the attribute is not a vector column, do not fill this field>,
            "enum": <enum of the parameter - Array of Strings | If no enum detected, do not fill this field>,
            "embedding_model": <embedding model of the parameter - String | If no embedding model detected, do not fill this field>,
            "expr": <if theres a expression for the parameters, like filter conditions, add it here. Use python basic operations or datetime operations | type: String | default: None | If unknown, do not fill this field>,
            "value": <if theres a static value for the parameters, like filter conditions, add it here | type: Any | default: None | If unknown, do not fill this field>,
            "info": <inform if the attribute is part of partitionk key, sorting key, indexed column or vector column | type: String | default: "">
        }},
    ],
    "method": "find",
    "table_name": <table name of the tool>,
    "db_name": <db name of the tool>,
    "limit": <limit of the tool | Default: 10>
}}