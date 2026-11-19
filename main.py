
import os
import re
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not configured")


app = FastAPI(
    title="n8n Workshop CRM API",
    description="CRM API for the n8n workshop",
    version="1.2.2"
)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    try:
        return psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


# --------------------------------------------------
# VALIDATION MODELS
# --------------------------------------------------

class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    budget: int = Field(ge=0)
    enquiry: str = Field(min_length=10, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters.")

        return value

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None:
            return None

        if isinstance(value, str) and not value.strip():
            return None

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return None

        digits = re.sub(r"\D", "", value)

        if len(digits) < 10:
            raise ValueError(
                "Phone number must contain at least 10 digits."
            )

        return value.strip()

    @field_validator("enquiry")
    @classmethod
    def validate_enquiry(cls, value):
        value = value.strip()

        if len(value) < 10:
            raise ValueError(
                "Enquiry must contain at least 10 characters."
            )

        return value


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    budget: Optional[int] = Field(default=None, ge=0)
    enquiry: Optional[str] = Field(default=None, min_length=10, max_length=2000)
    status: Optional[str] = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is None:
            return None

        value = value.strip()

        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters.")

        return value

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None:
            return None

        if isinstance(value, str) and not value.strip():
            return None

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return None

        digits = re.sub(r"\D", "", value)

        if len(digits) < 10:
            raise ValueError(
                "Phone number must contain at least 10 digits."
            )

        return value.strip()

    @field_validator("enquiry")
    @classmethod
    def validate_enquiry(cls, value):
        if value is None:
            return None

        value = value.strip()

        if len(value) < 10:
            raise ValueError(
                "Enquiry must contain at least 10 characters."
            )

        return value


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.2.2"
        }

    finally:
        connection.close()


# --------------------------------------------------
# CREATE LEAD
# --------------------------------------------------

@app.post("/leads", status_code=201)
def create_lead(lead: LeadCreate):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO leads (
                name,
                email,
                phone,
                budget_amount,
                enquiry
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                lead.name,
                str(lead.email),
                lead.phone,
                lead.budget,
                lead.enquiry
            )
        )

        new_lead = cursor.fetchone()
        connection.commit()

        return new_lead

    except Exception as e:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not create lead: {str(e)}"
        )

    finally:
        connection.close()


# --------------------------------------------------
# GET ALL LEADS
# --------------------------------------------------

@app.get("/leads")
def get_leads():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM leads
            ORDER BY created_at DESC
            """
        )

        leads = cursor.fetchall()

        return leads

    finally:
        connection.close()


# --------------------------------------------------
# GET SINGLE LEAD
# --------------------------------------------------

@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM leads
            WHERE id = %s
            """,
            (lead_id,)
        )

        lead = cursor.fetchone()

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        return lead

    finally:
        connection.close()


# --------------------------------------------------
# UPDATE LEAD
# --------------------------------------------------

@app.patch("/leads/{lead_id}")
def update_lead(lead_id: int, lead: LeadUpdate):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        update_data = lead.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        # API field name -> database column name
        column_mapping = {
            "budget": "budget_amount"
        }

        allowed_columns = {
            "name",
            "email",
            "phone",
            "budget",
            "enquiry",
            "status"
        }

        fields = []
        values = []

        for field, value in update_data.items():
            if field not in allowed_columns:
                continue

            column = column_mapping.get(field, field)

            fields.append(f"{column} = %s")

            if field == "email" and value is not None:
                value = str(value)

            values.append(value)

        if not fields:
            raise HTTPException(
                status_code=400,
                detail="No valid fields provided"
            )

        values.append(lead_id)

        query = f"""
            UPDATE leads
            SET {", ".join(fields)}
            WHERE id = %s
            RETURNING *
        """

        cursor.execute(query, tuple(values))

        updated_lead = cursor.fetchone()

        if not updated_lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        connection.commit()

        return updated_lead

    except HTTPException:
        connection.rollback()
        raise

    except Exception as e:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not update lead: {str(e)}"
        )

    finally:
        connection.close()


# --------------------------------------------------
# DELETE LEAD
# --------------------------------------------------

@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: int):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM leads
            WHERE id = %s
            RETURNING id
            """,
            (lead_id,)
        )

        deleted_lead = cursor.fetchone()

        if not deleted_lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        connection.commit()

        return {
            "message": "Lead deleted successfully",
            "id": deleted_lead["id"]
        }

    except HTTPException:
        connection.rollback()
        raise

    except Exception as e:
        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not delete lead: {str(e)}"
        )

    finally:
        connection.close()
