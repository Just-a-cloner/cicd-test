from flask import Flask, request, jsonify, g
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
import os
import random
import time
from datetime import datetime
from functools import wraps

from config import Config, TestConfig
from models import db, User, Fact, Favorite, ApiUsage

load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    jwt = JWTManager(app)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per hour", "50 per minute"]
    )
    limiter.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    def track_usage(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            user_id = None
            
            try:
                user_id = get_jwt_identity()
            except:
                pass
            
            try:
                response = f(*args, **kwargs)
                response_code = 200
                if hasattr(response, 'status_code'):
                    response_code = response.status_code
            except Exception as e:
                response_code = 500
                response = {'error': 'Internal server error'}, 500
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            usage = ApiUsage(
                endpoint=request.endpoint,
                method=request.method,
                ip_address=request.remote_addr,
                user_id=user_id,
                response_code=response_code,
                response_time_ms=response_time
            )
            
            try:
                db.session.add(usage)
                db.session.commit()
            except:
                db.session.rollback()
            
            return response
        return decorated_function
    
    def seed_data():
        if Fact.query.count() == 0:
            facts_data = [
                ("Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "food"),
                ("A group of flamingos is called a 'flamboyance'.", "animals"),
                ("Octopuses have three hearts and blue blood.", "animals"),
                ("Bananas are berries, but strawberries aren't.", "food"),
                ("A single cloud can weigh more than a million pounds.", "nature"),
                ("Sharks have existed longer than trees.", "animals"),
                ("The human brain uses about 20% of the body's total energy.", "science"),
                ("There are more possible games of chess than atoms in the observable universe.", "science"),
                ("Wombat poop is cube-shaped.", "animals"),
                ("The shortest war in history lasted only 38-45 minutes.", "history"),
                ("The Great Wall of China isn't visible from space with the naked eye.", "history"),
                ("A group of owls is called a parliament.", "animals"),
                ("Cleopatra lived closer to the Moon landing than to the construction of the Great Pyramid.", "history"),
                ("The longest word in English has 189,819 letters and takes over 3 hours to pronounce.", "language"),
                ("Your stomach gets an entirely new lining every 3-5 days.", "science")
            ]
            
            for content, category in facts_data:
                fact = Fact(content=content, category=category)
                db.session.add(fact)
            
            try:
                db.session.commit()
            except:
                db.session.rollback()
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Rate limit exceeded', 'retry_after': str(e.retry_after)}), 429
    
    @app.route('/')
    @track_usage
    def home():
        fact = Fact.query.filter_by(is_active=True).order_by(db.func.random()).first()
        fact_data = fact.to_dict() if fact else "No facts available"
        
        return jsonify({
            'message': 'Welcome to the Enhanced Random Facts API',
            'fact': fact_data,
            'endpoints': {
                'authentication': ['/register', '/login'],
                'facts': ['/facts', '/facts/random', '/facts/category/<category>'],
                'user': ['/favorites', '/profile'],
                'admin': ['/admin/stats', '/admin/facts']
            }
        })
    
    @app.route('/health')
    @track_usage
    def health_check():
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            db_status = 'unhealthy'
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Service is running'
        })
    
    @app.route('/register', methods=['POST'])
    @limiter.limit("5 per minute")
    @track_usage
    def register():
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        
        db.session.add(user)
        try:
            db.session.commit()
            return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201
        except:
            db.session.rollback()
            return jsonify({'error': 'Failed to create user'}), 500
    
    @app.route('/login', methods=['POST'])
    @limiter.limit("10 per minute")
    @track_usage
    def login():
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Missing username or password'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']) and user.is_active:
            access_token = create_access_token(identity=user.id)
            return jsonify({'access_token': access_token, 'user': user.to_dict()})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    @app.route('/facts')
    @track_usage
    def get_facts():
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        category = request.args.get('category')
        
        query = Fact.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        
        facts = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'facts': [fact.to_dict() for fact in facts.items],
            'pagination': {
                'page': page,
                'pages': facts.pages,
                'per_page': per_page,
                'total': facts.total
            }
        })
    
    @app.route('/facts/random')
    @track_usage
    def random_fact():
        category = request.args.get('category')
        query = Fact.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        fact = query.order_by(db.func.random()).first()
        
        if not fact:
            return jsonify({'error': 'No facts found'}), 404
        
        fact.view_count += 1
        try:
            db.session.commit()
        except:
            db.session.rollback()
        
        return jsonify(fact.to_dict())
    
    @app.route('/facts/categories')
    @track_usage
    def get_categories():
        categories = db.session.query(Fact.category).filter_by(is_active=True).distinct().all()
        return jsonify({'categories': [cat[0] for cat in categories]})
    
    @app.route('/favorites', methods=['GET', 'POST', 'DELETE'])
    @jwt_required()
    @track_usage
    def manage_favorites():
        user_id = get_jwt_identity()
        
        if request.method == 'GET':
            favorites = db.session.query(Favorite, Fact).join(Fact).filter(
                Favorite.user_id == user_id,
                Fact.is_active == True
            ).all()
            return jsonify([fact.to_dict() for _, fact in favorites])
        
        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'fact_id' not in data:
                return jsonify({'error': 'Missing fact_id'}), 400
            
            fact = Fact.query.get(data['fact_id'])
            if not fact or not fact.is_active:
                return jsonify({'error': 'Fact not found'}), 404
            
            existing = Favorite.query.filter_by(user_id=user_id, fact_id=data['fact_id']).first()
            if existing:
                return jsonify({'error': 'Already in favorites'}), 400
            
            favorite = Favorite(user_id=user_id, fact_id=data['fact_id'])
            db.session.add(favorite)
            try:
                db.session.commit()
                return jsonify({'message': 'Added to favorites'}), 201
            except:
                db.session.rollback()
                return jsonify({'error': 'Failed to add favorite'}), 500
        
        elif request.method == 'DELETE':
            data = request.get_json()
            if not data or 'fact_id' not in data:
                return jsonify({'error': 'Missing fact_id'}), 400
            
            favorite = Favorite.query.filter_by(user_id=user_id, fact_id=data['fact_id']).first()
            if not favorite:
                return jsonify({'error': 'Not in favorites'}), 404
            
            db.session.delete(favorite)
            try:
                db.session.commit()
                return jsonify({'message': 'Removed from favorites'})
            except:
                db.session.rollback()
                return jsonify({'error': 'Failed to remove favorite'}), 500
    
    @app.route('/profile')
    @jwt_required()
    @track_usage
    def get_profile():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        favorites_count = Favorite.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'user': user.to_dict(),
            'favorites_count': favorites_count
        })
    
    @app.route('/admin/stats')
    @jwt_required()
    @track_usage
    def admin_stats():
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'total_facts': Fact.query.count(),
            'active_facts': Fact.query.filter_by(is_active=True).count(),
            'total_favorites': Favorite.query.count(),
            'api_calls_today': ApiUsage.query.filter(
                ApiUsage.timestamp >= datetime.utcnow().date()
            ).count()
        }
        
        return jsonify(stats)
    
    with app.app_context():
        db.create_all()
        seed_data()
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)