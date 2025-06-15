# muni_admin/chatbot_logic.py

import os
import re
import logging
from django.conf import settings
from Citoyen.models import Problem, Complaint, Category # Import your municipal models

# --- LangChain Imports ---
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import sqlalchemy

# --- Configure Logger and LLMs (keep as is) ---
logger = logging.getLogger(__name__)
sql_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=settings.GEMINI_API_KEY)
response_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5, google_api_key=settings.GEMINI_API_KEY)


# muni_admin/chatbot_logic.py

def create_sql_query_chain(db, llm, municipality_id):
    """
    Creates a LangChain chain to generate a SQL query compatible with your database.
    This prompt is now tailored for municipal administration.
    """
    # The template is now a regular multi-line string, not an f-string, to avoid confusion.
    # The .format() method is used at the end for clarity.
    template = """
    You are an expert data analyst for a municipal administration, fluent in SQL.
    Based on the table schema below, write a well-formed SQL query that would answer the user's question.
    The user is an administrator for the municipality with ID: {municipality_id}.

    <SCHEMA>{{schema}}</SCHEMA>

    ### IMPORTANT RULES ###
    1.  **SECURITY**: All queries on `Citoyen_problem` or `Citoyen_complaint` MUST include a `WHERE municipality_id = {municipality_id}` clause. This is a mandatory security rule.
    2.  Use backticks (`) around all table and column names (e.g., `Citoyen_problem`).
    3.  Limit results to 5 with `LIMIT 5` unless the user asks for a different number.
    4.  Only select relevant columns. Do not use `SELECT *`.
    5.  If the question is not related to municipal data (problems, complaints, citizens), return:
        SELECT 'Cette question ne concerne pas les données de la municipalité.' AS Response;

    ### EXAMPLE QUERY ###
    Question: Montre-moi les 3 problèmes les plus récents qui sont encore en attente.
    SQL Query: SELECT `description`, `status`, `created_at` FROM `Citoyen_problem` WHERE `status` = 'PENDING' AND `municipality_id` = {municipality_id} ORDER BY `created_at` DESC LIMIT 3;

    Question: {{question}}
    SQL Query:
    """
    
    # We format the string here to inject the municipality_id
    # The other placeholders {schema} and {question} will be handled by LangChain
    formatted_template = template.format(municipality_id=municipality_id)

    prompt = ChatPromptTemplate.from_template(formatted_template)

    return (
        RunnablePassthrough.assign(schema=lambda _: db.get_table_info())
        | prompt
        | llm
        | StrOutputParser()
    )
def create_full_chain(db, sql_query_chain, response_llm):
    """
    Creates the full chain: generates SQL, executes it, and generates a natural language response.
    This prompt is now tailored for interpreting municipal data.
    """
    response_template = """
    You are a helpful assistant for a municipal administrator, interpreting SQL results.
    Based on the user's question, the generated SQL query, and the SQL response, write a concise, helpful, natural language answer.

    ### RULES ###
    1.  **LANGUAGE**: The answer MUST be in the same language as the user's "Question".
    2.  **UNRELATED QUESTION**: If the SQL Query is "SELECT 'Cette question ne concerne pas...", respond naturally in the user's language that you can only answer questions about municipal problems, complaints, etc.
    3.  **SQL ERROR**: If the SQL Response contains an error, politely inform the user in their language that there was an issue and they could try rephrasing. DO NOT show the query or the error.
    4.  **NORMAL RESPONSE**: Otherwise, synthesize the SQL Response into a clear answer based on the user's Question.
    5.  **NO DATA**: If the SQL Response is empty, state in the user's language that no matching data was found.

    User question: {question}
    SQL Query: <SQL>{query}</SQL>
    SQL Response: {response}

    Natural Language Response:
    """
    response_prompt = ChatPromptTemplate.from_template(response_template)
    
    def clean_sql(sql_query: str) -> str:
        cleaned = re.sub(r"^```(?:sql)?\s*", "", sql_query.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def safe_run_sql(query: str):
        cleaned_query = clean_sql(query)
        logger.info(f"Executing Cleaned SQL: {cleaned_query}")
        if not cleaned_query: return "Error: Empty SQL query."
        try:
            return db.run(cleaned_query)
        except Exception as e:
            logger.error(f"SQL Execution Error for query [{cleaned_query}]: {e}")
            return f"Error: Could not execute SQL query. Details: {e}"

    return (
        RunnablePassthrough.assign(query=sql_query_chain)
        .assign(response=RunnableLambda(lambda vars: safe_run_sql(vars["query"])))
        | response_prompt
        | response_llm
        | StrOutputParser()
    )


def get_chatbot_response(user_input, municipality_id):
    """
    Main function to get the chatbot response for the municipal admin app.
    """
    logger.info(f"Chatbot request for municipality {municipality_id}: {user_input}")
    try:
        # 1. Setup Database Connection using Django's settings
        db_settings = settings.DATABASES['default']
        db_engine_name = db_settings['ENGINE'].split('.')[-1]
        
         # This mapping makes it work for common Django backends
        if db_engine_name == 'sqlite3':
            # For SQLite, the URI is just 'sqlite:///' followed by the file path.
            # Django's settings['NAME'] gives us the absolute path to db.sqlite3
            db_uri = f"sqlite:///{db_settings['NAME']}"
        elif db_engine_name == 'mysql':
            db_uri = f"mysql+mysqlconnector://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        elif db_engine_name == 'postgresql':
            db_uri = f"postgresql+psycopg2://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        else:
            raise ValueError(f"Unsupported database engine: {db_engine_name}")
        # 2. Specify relevant tables for your Muni_admin app
        # NOTE: Django creates table names as `appname_modelname`
        relevant_tables = [
            'Citoyen_problem', 
            'Citoyen_complaint', 
            'Citoyen_category', 
            'Citoyen_citizen',
            'Citoyen_statuslog'
        ]
        
        db = SQLDatabase.from_uri(db_uri, include_tables=relevant_tables, sample_rows_in_table_info=0)

        # 3. Create and Invoke Chains, passing the municipality_id for security
        sql_chain = create_sql_query_chain(db, sql_llm, municipality_id)
        full_chain = create_full_chain(db, sql_chain, response_llm)

        response = full_chain.invoke({"question": user_input})
        logger.info(f"Generated NL response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}", exc_info=True)
        return "Désolé, une erreur interne s'est produite lors du traitement de votre demande."