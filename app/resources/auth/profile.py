from flask import jsonify
from flask_restful import Resource
from flask import request
from app.models.user import User
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity

class ProfileController(Resource):
    
    @jwt_required()
    def get(self): 
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
        current_user = get_jwt_identity()
        print(current_user)
        
        user = User.query.filter(User.id == int(current_user)).first()
        
        response = { 
          "id": user.id,
          "username": user.username,
          "email": user.email,
          "name": user.name,
          "phone": user.phone,
          "role": user.role,
          "roles": user.roles()
        }
        return jsonify(response)
    
