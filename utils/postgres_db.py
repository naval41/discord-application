import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import uuid
from datetime import datetime

class PostgresDB:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            self.db_config = config["postgres"]
        
    def get_connection(self):
        return psycopg2.connect(
            host=self.db_config["host"],
            user=self.db_config["user"],
            password=self.db_config["password"],
            database=self.db_config["database"],
            port=self.db_config["port"]
        )

    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchone()
        finally:
            conn.close()

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
        finally:
            conn.close()

    def execute_commit(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                return cur.rowcount
        finally:
            conn.close()

    def get_or_create_company(self, name, slug, description=None, website=None, logo_url=None):
        # Check if exists
        query = "SELECT * FROM public.\"Company\" WHERE slug = %s"
        company = self.fetch_one(query, (slug,))
        
        if company:
            return company

        # Create new
        new_id = str(uuid.uuid4())
        insert_query = """
            INSERT INTO public."Company" (
                id, name, slug, description, website, "logoUrl", "updatedAt", "createdBy", "updatedBy", "createdAt"
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'system', 'system', NOW())
        """
        self.execute_commit(insert_query, (
            new_id, name, slug, description or "", website, logo_url
        ))
        
        return self.fetch_one(query, (slug,))

    def get_job_role_by_name(self, name):
         # Try exact match or ilike
        query = "SELECT * FROM public.\"JobRole\" WHERE name ILIKE %s LIMIT 1"
        return self.fetch_one(query, (f"%{name}%",))

    def get_job_roles_for_company(self, company_id):
        query = """
            SELECT jr.id, jr.name, jr.slug, jp.name as profile_name
            FROM public."JobRole" jr
            JOIN public."JobProfile" jp ON jr."jobProfileId" = jp.id
            WHERE jp."companyId" = %s
        """
        return self.fetch_all(query, (company_id,))

    def create_interview(self, data):
        new_id = str(uuid.uuid4())
        query = """
            INSERT INTO public."Interview" (
                id, "companyId", "userId", "jobRoleId", slug, title, location, date, difficulty, 
                "noOfRounds", "interviewProcess", "preparationSources", "overallRating", 
                "isAnonymous", status, "offerStatus", "createdAt", "updatedAt", "createdBy", "updatedBy"
            ) VALUES (
                %(id)s, %(companyId)s, %(userId)s, %(jobRoleId)s, %(slug)s, %(title)s, %(location)s, %(date)s, %(difficulty)s,
                %(noOfRounds)s, %(interviewProcess)s, %(preparationSources)s, %(overallRating)s,
                %(isAnonymous)s, %(status)s, %(offerStatus)s, NOW(), NOW(), 'system', 'system'
            )
        """
        data['id'] = new_id
        # Use a default user ID if none provided (e.g. system bot user) - TO BE HANDLED BY CALLER or Config
        # For now, we assume the caller provides a valid userId or we pick one.
        # IF userId is missing, we might need a fallback.
        
        self.execute_commit(query, data)
        return new_id

    def create_interview_round(self, data):
        new_id = str(uuid.uuid4())
        query = """
            INSERT INTO public."InterviewRound" (
                id, "interviewId", name, duration, difficulty, experience, "keyTakeaways", 
                "orderIndex", "createdAt", "updatedAt"
            ) VALUES (
                %(id)s, %(interviewId)s, %(name)s, %(duration)s, %(difficulty)s, %(experience)s, %(keyTakeaways)s,
                %(orderIndex)s, NOW(), NOW()
            )
        """
        data['id'] = new_id
        self.execute_commit(query, data)
        return new_id
