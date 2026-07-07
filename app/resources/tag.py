from flask import make_response, jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.models.tag import Tag
from app.models import db
from app.schemas.tag import TagSchema
from pydantic import ValidationError

class TagResource(Resource):
    
    @jwt_required()
    def get(self, id=None):
        if id:
            tag = Tag.query.get(id)
            if not tag:
                return make_response(jsonify({'success': False, 'message': 'Tag not found'}), 404)
            return make_response(jsonify({'success': True, 'data': tag.to_dict()}), 200)
        
        # Get pagination parameters
        
        full = request.args.get('full')
        if not full:
            # Get paginated results
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 25, type=int)
            query = request.args.get('q', type=str)
            if query:
                pagination = Tag.query.filter(Tag.name.ilike(f'%{query}%')).paginate(page=page, per_page=per_page, error_out=False)
            else:
                pagination = Tag.query.paginate(page=page, per_page=per_page, error_out=False)
            
            return make_response(jsonify({
                'data': [tag.to_dict(True) for tag in pagination.items],
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }), 200)
        else:
            tags = Tag.query.filter_by(parent_id=None).all()
            return make_response(jsonify({'success': True, 'data': [tag.to_dict() for tag in tags]}), 200)

    @jwt_required()
    def post(self):
        try:
            data = request.json
            tag_data = TagSchema(**data)
            
            tag = Tag(**tag_data.model_dump())
            db.session.add(tag)
            db.session.commit()

            return make_response(jsonify({
                'success': True,
                'message': 'Tag created successfully',
                'data': tag.to_dict()
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
            tag = Tag.query.get(id)
            if not tag:
                return make_response(jsonify({'success': False, 'message': 'Tag not found'}), 404)

            data = request.json
            tag_data = TagSchema(**data)
            
            for key, value in tag_data.model_dump().items():
                setattr(tag, key, value)
            
            db.session.commit()

            return make_response(jsonify({
                'success': True,
                'message': 'Tag updated successfully',
                'data': tag.to_dict()
            }), 200)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def delete(self, id):
        tag = Tag.query.get(id)
        if not tag:
            return make_response(jsonify({'success': False, 'message': 'Tag not found'}), 404)

        db.session.delete(tag)
        db.session.commit()
        
        return make_response(jsonify({'success': True, 'message': 'Tag deleted successfully'}), 200)
