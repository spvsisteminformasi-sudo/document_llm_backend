from flask import jsonify, make_response
from flask_restful import Resource
from flask import request
from app.models.user import User
from app.models import db
from app.schemas.auth import RegisterSchema
from pydantic import ValidationError

class RegisterController(Resource):
    def post(self):
        """Authenticates a user and returns an access token."""
        try:
            data = request.json
            register_data = RegisterSchema(**data)
            
            if User.query.filter(User.username == register_data.username).first():
                return make_response(jsonify({"message": "A user with that username already exists."}), 409)
                
            if User.query.filter(User.email == register_data.email).first():
                return make_response(jsonify({"message": "A user with that email already exists."}), 409)

            user = User(
                username=register_data.username,
                email=register_data.email,
                name=register_data.name,
                phone=register_data.phone,
                role='User'  # Default role, can be changed later
            )
            user.set_password(register_data.password)
            
            db.session.add(user)
            db.session.commit()
            
            return make_response(jsonify({
                "success": True,
                "message": "User created successfully."
            }), 201)

        except ValidationError as e:
            return make_response(jsonify({
                "success": False,
                "message": "Validation error",
                "errors": e.errors()
            }), 400)

