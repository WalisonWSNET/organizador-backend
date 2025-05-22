from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from src.models.user import User, db
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Verificar se os campos obrigatórios estão presentes
    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'message': 'Campos obrigatórios ausentes'}), 400
    
    # Verificar se o usuário já existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Nome de usuário já existe'}), 409
    
    # Verificar se o email já existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email já cadastrado'}), 409
    
    # Criar hash da senha
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Criar novo usuário
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        is_admin=data.get('is_admin', False)  # Por padrão, usuários não são admin
    )
    
    # Salvar no banco de dados
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Usuário registrado com sucesso'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Verificar se os campos obrigatórios estão presentes
    if not all(k in data for k in ['username', 'password']):
        return jsonify({'message': 'Campos obrigatórios ausentes'}), 400
    
    # Buscar usuário pelo nome de usuário
    user = User.query.filter_by(username=data['username']).first()
    
    # Verificar se o usuário existe e a senha está correta
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Criar token JWT com validade de 1 dia
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'is_admin': user.is_admin},
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'message': 'Credenciais inválidas'}), 401

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    # Obter ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Buscar usuário no banco de dados
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    # Obter ID do usuário a partir do token JWT
    user_id = get_jwt_identity()
    
    # Buscar usuário no banco de dados
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    data = request.get_json()
    
    # Atualizar campos permitidos
    if 'email' in data:
        # Verificar se o email já está em uso por outro usuário
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'message': 'Email já está em uso'}), 409
        user.email = data['email']
    
    if 'password' in data:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Salvar alterações
    db.session.commit()
    
    return jsonify({'message': 'Perfil atualizado com sucesso', 'user': user.to_dict()}), 200
