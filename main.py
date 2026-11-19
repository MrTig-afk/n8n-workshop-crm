
import os
import re
from contextlib import contextmanager
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator

DATABASE_URL = os.environ.get("DATABASE_URL")

app = FastAPI(
    title="Workshop CRM API",
    description="A simple practice CRM API for the n8n workshop.",
    version="1.2.0",
)


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not configured.")

    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# Request model for creating a lead
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

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is not None:
            digits = re.sub(r"\D", "", value)
            if len(digits) < 10:
                raise ValueError("Phone number must contain at least 10 digits.")
        return value

    @field_validator("enquiry")
    @classmethod
    def validate_enquiry(cls, value):
        value = value.strip()
        if len(value) < 10:
            raise ValueError("Enquiry must contain at least 10 characters.")
        return value


# Request model for updating a lead
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
        if value is not None:
            value = value.strip()
            if len(value) < 2:
                raise ValueError("Name must contain at least 2 characters.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is not None:
            digits = re.sub(r"\D", "", value)
            if len(digits) < 10:
                raise ValueError("Phone number must contain at least 10 digits.")
        return value

    @field_validator("enquiry")
    @classmethod
    def validate_enquiry(cls, value):
        if value is not None:
            value = value.strip()
            if len(value) < 10:
                raise ValueError("Enquiry must contain at least 10 characters.")
        return value


@app.get("/")
def root():
    return {
        "message": "Workshop CRM API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed."
        ) from exc


# CREATE a lead
@app.post("/leads", status_code=status.HTTP_201_CREATED)
def create_lead(lead: LeadCreate):
    with get_connection() as conn:
        row = conn.execute(
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
                lead.enquiry,
            ),
        ).fetchone()

    return row


# READ all leads
@app.get("/leads")
def get_leads():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id"
        ).fetchall()

    return rows


# READ one lead
@app.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE id = %s",
            (lead_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found."
        )

    return row


# UPDATE a lead
@app.patch("/leads/{lead_id}")
def update_lead(lead_id: int, lead: LeadUpdate):
    updates = lead.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update."
        )

    # Map the API field "budget" to the database column "budget_amount"
    column_mapping = {
        "budget": "budget_amount"
    }

    allowed_fields = {
        "name",
        "email",
        "phone",
        "budget",
        "enquiry",
        "status",
    }

    fields = [
        field for field in updates
        if field in allowed_fields
    ]

    assignments = ", ".join(
        f"{column_mapping.get(field, field)} = %s"
        for field in fields
    )

    values = [
        str(updates[field])
        if field == "email" and updates[field] is not None
        else updates[field]
        for field in fields
    ]

    values.append(lead_id)

    with get_connection() as conn:
        row = conn.execute(
            f"""
            UPDATE leads
            SET {assignments}
            WHERE id = %s
            RETURNING *
            """,
            values,
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found."
        )

    return row


# DELETE a lead
@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "DELETE FROM leads WHERE id = %s RETURNING *",
            (lead_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found."
        )

    return {
        "message": "Lead deleted",
        "lead": row
    }
