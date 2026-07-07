import os
from flask import jsonify, make_response
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from flask import request
from app.models.user import User
from werkzeug.security import check_password_hash
from datetime import timedelta
import requests  # For verifying reCAPTCHA

class LoginController(Resource):
    
    def post(self): 
        """
        Authenticates a user and returns an access token.
        ---
        tags:
          - Authentication
        responses:
          200:
            description: A successful response with the access token.
          401:
            description: Unauthorized, invalid credentials.
        """
        # Verify reCAPTCHA
        # recaptcha_token = request.json.get("recaptcha", None)
        # if not recaptcha_token:
        #     return make_response(jsonify({"message": "reCAPTCHA token is missing"}), 400)

        # recaptcha_secret = os.getenv('RECAPTCHA_SECRET_KEY')  # Replace with your reCAPTCHA secret key
        # recaptcha_response = requests.post(
        #     "https://www.google.com/recaptcha/api/siteverify",
        #     data={"secret": recaptcha_secret, "response": recaptcha_token}
        # )
        # recaptcha_result = recaptcha_response.json()

        # if not recaptcha_result.get("success", False):
        #     return make_response(jsonify({"message": "Invalid reCAPTCHA"}), 400)

        email = request.json.get("email", None)
        password = request.json.get("password", None)
        user = User.query.filter(
            User.email == email
        ).first()

        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=12))
            response = { 
              "access_token": access_token, 
              "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "roles": user.roles()
              }
            }
            return jsonify(response)

        return make_response(jsonify({"message": "Bad username or password"}), 401)

