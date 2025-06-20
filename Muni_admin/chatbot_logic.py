# muni_admin/chatbot_logic.py

import os
import re
import logging
from django.conf import settings
from Citoyen.models import Problem, Complaint, Category, Citizen, Municipality
from django.db.models import Q, Count, Max

# --- LangChain Imports ---
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import sqlalchemy

# --- Configure Logger and LLMs ---
logger = logging.getLogger(__name__)
sql_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, google_api_key=settings.GEMINI_API_KEY)
response_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, google_api_key=settings.GEMINI_API_KEY)

def detect_language(text):
    """Simple language detection based on common words"""
    french_words = ['le', 'la', 'les', 'de', 'des', 'du', 'et', 'est', 'dans', 'pour', 'avec', 'sur', 'par', 'une', 'un', 'ce', 'cette', 'ses', 'son', 'sa', 'que', 'qui', 'quoi', 'comment', 'où', 'quand', 'pourquoi']
    english_words = ['the', 'and', 'is', 'in', 'for', 'with', 'on', 'by', 'a', 'an', 'this', 'that', 'what', 'who', 'how', 'where', 'when', 'why']
    
    text_lower = text.lower()
    french_count = sum(1 for word in french_words if word in text_lower)
    english_count = sum(1 for word in english_words if word in text_lower)
    
    return 'fr' if french_count > english_count else 'en'

def get_urgency_keywords():
    """Returns keywords that indicate urgency in both languages"""
    return {
        'fr': ['urgent', 'urgence', 'danger', 'dangereux', 'grave', 'critique', 'aidez', 'aide', 'secours', 'désespéré', 'mourir', 'tuer', 'blessé', 'accident', 'cassé', 'inondation', 'feu', 'incendie'],
        'en': ['urgent', 'emergency', 'danger', 'dangerous', 'serious', 'critical', 'help', 'rescue', 'desperate', 'dying', 'kill', 'injured', 'accident', 'broken', 'flood', 'fire']
    }

def create_sql_query_chain(db, llm, municipality_id):
    """
    Creates a LangChain chain to generate a SQL query compatible with your database.
    Enhanced with better security and data filtering.
    """
    
    # Get urgency keywords dynamically
    urgency_keywords = get_urgency_keywords()
    
    # Create LIKE conditions for all urgency keywords
    french_urgency_conditions = []
    english_urgency_conditions = []
    
    for keyword in urgency_keywords['fr']:
        french_urgency_conditions.append(f"LOWER(p.`description`) LIKE '%{keyword}%'")
    
    for keyword in urgency_keywords['en']:
        english_urgency_conditions.append(f"LOWER(p.`description`) LIKE '%{keyword}%'")
    
    # Combine all urgency conditions
    all_urgency_conditions = french_urgency_conditions + english_urgency_conditions
    urgency_sql_condition = " OR ".join(all_urgency_conditions)
    
    template = """
    You are an expert data analyst for a municipal administration, fluent in SQL.
    Based on the table schema below, write a well-formed SQL query that would answer the user's question.
    The user is an administrator for the municipality with ID: {municipality_id}.

    <SCHEMA>{{schema}}</SCHEMA>

    ### CRITICAL SECURITY RULES ###
    1. **MANDATORY FILTER**: ALL queries on `Citoyen_problem` or `Citoyen_complaint` MUST include `WHERE municipality_id = '{municipality_id}'`.
    2. **NO SENSITIVE DATA**: NEVER select phone numbers, emails, NNI, or addresses in your queries.
    3. **CITIZEN PRIVACY**: When referencing citizens, only use full_name, never personal identifiers.

    ### QUERY GUIDELINES ###
    4. Use backticks (`) around all table and column names.
    5. Limit results to 5 with `LIMIT 5` unless specifically asked for more.
    6. Only select relevant columns for the question asked.
    7. For urgency analysis, use the following comprehensive urgency condition: ({urgency_condition})
    8. When asking about specific citizens, join with Citoyen_citizen table using citizen_id.
    9. **IMPORTANT**: Always use table aliases and prefix column names to avoid ambiguity (e.g., p.created_at, c.created_at).
    10. **COLUMN DISAMBIGUATION**: When joining tables, always specify which table the column comes from using aliases.
    11. **STRING LITERALS**: Use single quotes for string literals in WHERE clauses.

    ### RESPONSE FOR UNRELATED QUESTIONS ###
    If the question is not about municipal data (problems, complaints, citizens, categories), return:
    SELECT 'UNRELATED_QUESTION' AS response_type;

    ### EXAMPLE QUERIES ###
    Question: "Quels sont les problèmes les plus urgents?"
    SQL: SELECT p.`description`, p.`status`, p.`created_at`, c.`full_name` as citizen_name 
         FROM `Citoyen_problem` p 
         JOIN `Citoyen_citizen` c ON p.`citizen_id` = c.`id`
         WHERE p.`municipality_id` = '{municipality_id}' 
         AND ({urgency_condition})
         ORDER BY p.`created_at` DESC LIMIT 5;

    Question: "What are the most urgent problems?"
    SQL: SELECT p.`description`, p.`status`, p.`created_at`, c.`full_name` as citizen_name 
         FROM `Citoyen_problem` p 
         JOIN `Citoyen_citizen` c ON p.`citizen_id` = c.`id`
         WHERE p.`municipality_id` = '{municipality_id}' 
         AND ({urgency_condition})
         ORDER BY p.`created_at` DESC LIMIT 5;

    Question: "What is the latest problem for John Doe?"
    SQL: SELECT p.`description`, p.`status`, p.`created_at` 
         FROM `Citoyen_problem` p 
         JOIN `Citoyen_citizen` c ON p.`citizen_id` = c.`id`
         WHERE p.`municipality_id` = '{municipality_id}' 
         AND c.`full_name` LIKE '%John Doe%'
         ORDER BY p.`created_at` DESC LIMIT 1;

    Question: "Combien de problèmes sont en attente?"
    SQL: SELECT COUNT(*) as pending_count
         FROM `Citoyen_problem` p
         WHERE p.`municipality_id` = '{municipality_id}'
         AND p.`status` = 'PENDING';

    Question: "Quelles sont les catégories les plus fréquentes?"
    SQL: SELECT cat.`name`, COUNT(p.`id`) as problem_count
         FROM `Citoyen_problem` p
         JOIN `Citoyen_category` cat ON p.`category_id` = cat.`id`
         WHERE p.`municipality_id` = '{municipality_id}'
         GROUP BY cat.`id`, cat.`name`
         ORDER BY problem_count DESC LIMIT 5;

    Question: {{question}}
    SQL Query:
    """
    
    formatted_template = template.format(
        municipality_id=municipality_id,
        urgency_condition=urgency_sql_condition
    )
    prompt = ChatPromptTemplate.from_template(formatted_template)

    return (
        RunnablePassthrough.assign(schema=lambda _: db.get_table_info())
        | prompt
        | llm
        | StrOutputParser()
    )

def create_full_chain(db, sql_query_chain, response_llm):
    """
    Creates the full chain with improved response generation and language handling.
    """
    response_template = """
    You are a helpful multilingual assistant for a municipal administrator.
    Based on the user's question, SQL query, and results, provide a clear, helpful response.

    ### LANGUAGE RULES ###
    - Respond in the SAME language as the user's question
    - If user asks in French, respond in French
    - If user asks in English, respond in English

    ### RESPONSE GUIDELINES ###
    1. **UNRELATED**: If SQL response is 'UNRELATED_QUESTION', politely explain you only handle municipal data questions.
    2. **SQL ERROR**: If there's an error, apologize and suggest rephrasing - DON'T show technical details.
    3. **NO DATA**: If results are empty or show "[]" or no results, clearly state no matching data was found.
    4. **NORMAL RESPONSE**: Use ACTUAL data from the SQL results - never use placeholders like [description] or [citizen_name].
    5. **PRIVACY**: Never mention or display sensitive information like phone numbers, emails, or IDs.
    6. **FORMAT DATA**: Present the actual data in a clear, readable format with real values.

    ### URGENCY ANALYSIS ###
    When discussing urgent problems, highlight the urgency indicators and suggest immediate attention.

    ### IMPORTANT ###
    - NEVER use placeholder text like [description du problème 1] or [citizen_name]
    - ALWAYS use the actual data returned from the SQL query
    - If no data is returned, clearly state "Aucun résultat trouvé" or "No results found"

    User question: {question}
    SQL Query: <SQL>{query}</SQL>
    SQL Response: {response}

    Response (in the same language as the question, using REAL data from SQL results):
    """
    
    response_prompt = ChatPromptTemplate.from_template(response_template)
    
    def clean_sql(sql_query: str) -> str:
        cleaned = re.sub(r"^```(?:sql)?\s*", "", sql_query.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def safe_run_sql(query: str):
        cleaned_query = clean_sql(query)
        logger.info(f"Executing SQL: {cleaned_query}")
        
        if not cleaned_query:
            return "Error: Empty query"
            
        # Additional security check - ensure municipality filter exists
        if ('citoyen_problem' in cleaned_query.lower() or 'citoyen_complaint' in cleaned_query.lower()):
            if 'municipality_id' not in cleaned_query.lower():
                logger.warning("Query missing municipality_id filter - blocking for security")
                return "Error: Security violation - municipality filter required"
        
        try:
            result = db.run(cleaned_query)
            logger.info(f"SQL Result: {result}")
            
            # Add more detailed logging
            if not result or result == "[]" or len(str(result).strip()) == 0:
                logger.warning("SQL query returned empty results")
                return "No data found"
            
            return result
        except Exception as e:
            logger.error(f"SQL Error: {e}")
            return f"Error: Database query failed - {str(e)}"

    return (
        RunnablePassthrough.assign(query=sql_query_chain)
        .assign(response=RunnableLambda(lambda vars: safe_run_sql(vars["query"])))
        | response_prompt
        | response_llm
        | StrOutputParser()
    )

def get_chatbot_response(user_input, municipality_id):
    """
    Main function to get chatbot response with enhanced error handling and language support.
    """
    logger.info(f"Chatbot request for municipality {municipality_id}: {user_input}")
    
    # Detect user language
    user_language = detect_language(user_input)
    
    try:
        # First, let's try to get some basic data directly from Django ORM to verify data exists
        problem_count = Problem.objects.filter(municipality_id=municipality_id).count()
        logger.info(f"Direct Django ORM check - Problems found for municipality {municipality_id}: {problem_count}")
        
        if problem_count == 0:
            if user_language == 'fr':
                return f"Aucun problème trouvé pour votre municipalité (ID: {municipality_id}). Assurez-vous que des données ont été saisies dans le système."
            else:
                return f"No problems found for your municipality (ID: {municipality_id}). Please ensure data has been entered into the system."
        
        # Setup Database Connection
        db_settings = settings.DATABASES['default']
        db_engine_name = db_settings['ENGINE'].split('.')[-1]
        
        if db_engine_name == 'sqlite3':
            db_uri = f"sqlite:///{db_settings['NAME']}"
        elif db_engine_name == 'mysql':
            db_uri = f"mysql+mysqlconnector://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        elif db_engine_name == 'postgresql':
            db_uri = f"postgresql+psycopg2://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        else:
            raise ValueError(f"Unsupported database engine: {db_engine_name}")

        # Relevant tables for municipal admin
        relevant_tables = [
            'Citoyen_problem', 
            'Citoyen_complaint', 
            'Citoyen_category', 
            'Citoyen_citizen',
            'Citoyen_statuslog',
            'Citoyen_municipality'
        ]
        
        db = SQLDatabase.from_uri(db_uri, include_tables=relevant_tables, sample_rows_in_table_info=3)
        
        # Log database connection info
        logger.info(f"Database connected successfully. Available tables: {db.get_usable_table_names()}")

        # Create and invoke chains
        sql_chain = create_sql_query_chain(db, sql_llm, municipality_id)
        full_chain = create_full_chain(db, sql_chain, response_llm)

        response = full_chain.invoke({"question": user_input})
        logger.info(f"Generated response: {response}")
        return response

    except Exception as e:
        logger.error(f"Error in get_chatbot_response: {e}", exc_info=True)
        
        # Return error message in user's language
        if user_language == 'fr':
            return f"Désolé, une erreur s'est produite lors du traitement de votre demande: {str(e)}. Veuillez réessayer avec une formulation différente."
        else:
            return f"Sorry, an error occurred while processing your request: {str(e)}. Please try rephrasing your question."

def get_quick_stats(municipality_id):
    """
    Get quick statistics for the municipality dashboard
    """
    try:
        stats = {
            'total_problems': Problem.objects.filter(municipality_id=municipality_id).count(),
            'pending_problems': Problem.objects.filter(municipality_id=municipality_id, status='PENDING').count(),
            'total_complaints': Complaint.objects.filter(municipality_id=municipality_id).count(),
            'pending_complaints': Complaint.objects.filter(municipality_id=municipality_id, status='PENDING').count(),
            'urgent_problems': Problem.objects.filter(
                municipality_id=municipality_id,
                description__iregex=r'(urgent|danger|aide|secours|grave|critique)'
            ).count()
        }
        logger.info(f"Quick stats for municipality {municipality_id}: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        return None

def suggest_chatbot_questions(language='fr'):
    """
    Provide suggested questions for users
    """
    if language == 'fr':
        return [
            "Quels sont les problèmes les plus urgents ?",
            "Combien de réclamations sont en attente ?",
            "Quels sont les derniers problèmes signalés ?",
            "Quel est le statut des problèmes de cette semaine ?",
            "Quelles sont les catégories de problèmes les plus fréquentes ?"
        ]
    else:
        return [
            "What are the most urgent problems?",
            "How many complaints are pending?",
            "What are the latest reported problems?",
            "What is the status of this week's problems?",
            "What are the most frequent problem categories?"
        ]

# Add a debug function to test the database connection and data
def debug_database_connection(municipality_id):
    """
    Debug function to test database connection and data availability
    """
    try:
        # Test Django ORM access
        problems = Problem.objects.filter(municipality_id=municipality_id)[:5]
        logger.info(f"Django ORM - Found {problems.count()} problems")
        
        for problem in problems:
            logger.info(f"Problem: {problem.description[:50]}... | Status: {problem.status} | Created: {problem.created_at}")
        
        # Test LangChain database connection
        db_settings = settings.DATABASES['default']
        db_engine_name = db_settings['ENGINE'].split('.')[-1]
        
        if db_engine_name == 'sqlite3':
            db_uri = f"sqlite:///{db_settings['NAME']}"
        elif db_engine_name == 'mysql':
            db_uri = f"mysql+mysqlconnector://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        elif db_engine_name == 'postgresql':
            db_uri = f"postgresql+psycopg2://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        
        relevant_tables = ['Citoyen_problem', 'Citoyen_citizen']
        db = SQLDatabase.from_uri(db_uri, include_tables=relevant_tables)
        
        # Test direct SQL query
        test_query = f"SELECT COUNT(*) as count FROM `Citoyen_problem` WHERE `municipality_id` = '{municipality_id}'"
        result = db.run(test_query)
        logger.info(f"Direct SQL test - Result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Debug database connection failed: {e}", exc_info=True)
        return False