def user_entity(user) -> dict:
    return {
        "id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),

        # Personal Info
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "age": user.get("age"),
        "gender": user.get("gender"),
        "date_of_birth": user.get("date_of_birth"),

        # Employment Info
        "employee_id": user.get("employee_id"),
        "department_id": user.get("department_id"),
        "role": user.get("role"),
        "employment_type": user.get("employment_type"),
        "location": user.get("location"),
        "hire_date": user.get("hire_date"),
        "status": user.get("status"),

        # Goals
        "step_goal": user.get("step_goal"),
        "calorie_goal": user.get("calorie_goal"),
        "active_minute_goal": user.get("active_minute_goal"),

        # Metadata
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }
