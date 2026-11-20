
import os
import re
from typing import Optional
from datetime import date

import psycopg
from psycopg.rows import dict_row

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
    version="1.3.0"
)

# Allow the Cloudflare dashboard to read CRM data.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
# SUPPORT TICKET MODELS
# --------------------------------------------------

class SupportTicketCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=200)
    customer_email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    subject: str = Field(min_length=3, max_length=250)
    description: str = Field(min_length=10, max_length=5000)
    category: str = Field(default="other", max_length=50)
    priority: str = Field(default="medium", max_length=20)
    assigned_team: str = Field(default="unassigned", max_length=100)


class SupportTicketUpdate(BaseModel):
    customer_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    customer_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, min_length=3, max_length=250)
    description: Optional[str] = Field(default=None, min_length=10, max_length=5000)
    category: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=30)
    assigned_team: Optional[str] = Field(default=None, max_length=100)


# --------------------------------------------------
# APPOINTMENT REQUEST MODELS
# --------------------------------------------------

class AppointmentRequestCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=200)
    customer_email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    preferred_date: date
    purpose: str = Field(min_length=5, max_length=2000)


class AppointmentRequestUpdate(BaseModel):
    customer_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    customer_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    preferred_date: Optional[date] = None
    purpose: Optional[str] = Field(default=None, min_length=5, max_length=2000)
    status: Optional[str] = Field(default=None, max_length=30)


# --------------------------------------------------
# GENERAL ENQUIRY MODELS
# --------------------------------------------------

class GeneralEnquiryCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=200)
    customer_email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    message: str = Field(min_length=10, max_length=5000)


class GeneralEnquiryUpdate(BaseModel):
    customer_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    customer_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    message: Optional[str] = Field(default=None, min_length=10, max_length=5000)
    status: Optional[str] = Field(default=None, max_length=30)


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
            "version": "1.3.0"
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

        return dict(new_lead)

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

        return [dict(lead) for lead in leads]

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

        return dict(lead)

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

        return dict(updated_lead)

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



# --------------------------------------------------
# SUPPORT TICKETS
# --------------------------------------------------

@app.post("/support-tickets", status_code=201)
def create_support_ticket(ticket: SupportTicketCreate):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO support_tickets
            (customer_name, customer_email, phone, subject, description,
             category, priority, assigned_team)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
            (ticket.customer_name.strip(), str(ticket.customer_email), ticket.phone,
             ticket.subject.strip(), ticket.description.strip(), ticket.category,
             ticket.priority, ticket.assigned_team),
        )
        record = cursor.fetchone()
        connection.commit()
        return dict(record)
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not create support ticket: {str(e)}")
    finally:
        connection.close()


@app.get("/support-tickets")
def get_support_tickets():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM support_tickets ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


@app.get("/support-tickets/{ticket_id}")
def get_support_ticket(ticket_id: int):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM support_tickets WHERE id = %s", (ticket_id,))
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Support ticket not found")
        return dict(record)
    finally:
        connection.close()


@app.patch("/support-tickets/{ticket_id}")
def update_support_ticket(ticket_id: int, ticket: SupportTicketUpdate):
    data = ticket.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    allowed = {"customer_name", "customer_email", "phone", "subject", "description",
               "category", "priority", "status", "assigned_team"}
    fields, values = [], []
    for field, value in data.items():
        if field in allowed:
            fields.append(f"{field} = %s")
            values.append(str(value) if field == "customer_email" and value is not None else value)
    fields.append("updated_at = NOW()")
    values.append(ticket_id)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE support_tickets SET {', '.join(fields)} WHERE id = %s RETURNING *",
            tuple(values))
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Support ticket not found")
        connection.commit()
        return dict(record)
    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not update support ticket: {str(e)}")
    finally:
        connection.close()


# --------------------------------------------------
# APPOINTMENT REQUESTS
# --------------------------------------------------

@app.post("/appointments", status_code=201)
def create_appointment_request(appointment: AppointmentRequestCreate):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO appointment_requests
            (customer_name, customer_email, phone, preferred_date, purpose)
            VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (appointment.customer_name.strip(), str(appointment.customer_email),
             appointment.phone, appointment.preferred_date, appointment.purpose.strip()))
        record = cursor.fetchone()
        connection.commit()
        return dict(record)
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not create appointment request: {str(e)}")
    finally:
        connection.close()


@app.get("/appointments")
def get_appointment_requests():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM appointment_requests ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


@app.get("/appointments/{appointment_id}")
def get_appointment_request(appointment_id: int):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM appointment_requests WHERE id = %s", (appointment_id,))
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Appointment request not found")
        return dict(record)
    finally:
        connection.close()


@app.patch("/appointments/{appointment_id}")
def update_appointment_request(appointment_id: int, appointment: AppointmentRequestUpdate):
    data = appointment.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    allowed = {"customer_name", "customer_email", "phone", "preferred_date", "purpose", "status"}
    fields, values = [], []
    for field, value in data.items():
        if field in allowed:
            fields.append(f"{field} = %s")
            values.append(str(value) if field == "customer_email" and value is not None else value)
    fields.append("updated_at = NOW()")
    values.append(appointment_id)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE appointment_requests SET {', '.join(fields)} WHERE id = %s RETURNING *",
            tuple(values))
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Appointment request not found")
        connection.commit()
        return dict(record)
    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not update appointment request: {str(e)}")
    finally:
        connection.close()


# --------------------------------------------------
# GENERAL ENQUIRIES
# --------------------------------------------------

@app.post("/enquiries", status_code=201)
def create_general_enquiry(enquiry: GeneralEnquiryCreate):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO general_enquiries
            (customer_name, customer_email, phone, message)
            VALUES (%s, %s, %s, %s) RETURNING *""",
            (enquiry.customer_name.strip(), str(enquiry.customer_email),
             enquiry.phone, enquiry.message.strip()))
        record = cursor.fetchone()
        connection.commit()
        return dict(record)
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not create general enquiry: {str(e)}")
    finally:
        connection.close()


@app.get("/enquiries")
def get_general_enquiries():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM general_enquiries ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


@app.get("/enquiries/{enquiry_id}")
def get_general_enquiry(enquiry_id: int):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM general_enquiries WHERE id = %s", (enquiry_id,))
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="General enquiry not found")
        return dict(record)
    finally:
        connection.close()


@app.patch("/enquiries/{enquiry_id}")
def update_general_enquiry(enquiry_id: int, enquiry: GeneralEnquiryUpdate):
    data = enquiry.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    allowed = {"customer_name", "customer_email", "phone", "message", "status"}
    fields, values = [], []
    for field, value in data.items():
        if field in allowed:
            fields.append(f"{field} = %s")
            values.append(str(value) if field == "customer_email" and value is not None else value)
    fields.append("updated_at = NOW()")
    values.append(enquiry_id)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE general_enquiries SET {', '.join(fields)} WHERE id = %s RETURNING *",
            tuple(values))
        record = cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="General enquiry not found")
        connection.commit()
        return dict(record)
    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not update general enquiry: {str(e)}")
    finally:
        connection.close()
