from flask import make_response, jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.models import db
from app.schemas.user import UserSchema
from pydantic import ValidationError

class UserResource(Resource):
    
    @jwt_required()
    def get(self, id=None):
        if id:
            user = User.query.get(id)
            if not user:
                return make_response(jsonify({'success': False,'message': 'User not found'}), 404)
            return make_response(jsonify({'success': True,'data': user.to_dict()}), 200)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        query = request.args.get('q', type=str)
        if query:
            pagination = User.query.filter(User.username.ilike(f'%{query}%')).paginate(page=page, per_page=per_page, error_out=False)
        else:
            pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return make_response(jsonify({
            'data': [user.to_dict() for user in pagination.items],
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages
        }), 200)

    @jwt_required()
    def post(self):
        try:
            data = request.json
            user_data = UserSchema(**data)
            
            user = User(
                username=user_data.username,
                email=user_data.email,
                name=user_data.name,
                phone=user_data.phone,
                role=user_data.role,
            )
            if user_data.password:
               user.set_password(user_data.password)
            
            db.session.add(user)
            db.session.commit()

            return make_response(jsonify({
                'success': True,
                'message': 'User created successfully',
                'data': user.to_dict()
            }), 201)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def put(self, id):
        try:
            user = User.query.get(id)
            if not user:
                return make_response(jsonify({'success': False, 'message': 'User not found'}), 404)

            data = request.json
            user_data = UserSchema(**data)
            
            user.username = user_data.username
            user.email = user_data.email
            user.name = user_data.name
            user.phone = user_data.phone
            user.role = user_data.role
            
            if user_data.password:
                user.set_password(user_data.password)
            
            db.session.commit()

            return make_response(jsonify({
                'success': True,
                'message': 'User updated successfully',
                'data': user.to_dict()
            }), 200)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def delete(self, id):
        user = User.query.get(id)
        if not user:
            return make_response(jsonify({'success': False, 'message': 'User not found'}), 404)

        db.session.delete(user)
        db.session.commit()
        
        return make_response(jsonify({'success': True, 'message': 'User deleted successfully'}), 200)
