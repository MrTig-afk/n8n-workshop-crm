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
