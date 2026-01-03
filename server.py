# server.py
"""
Flask Backend API Sunucusu - Bulut Senkronizasyonu için
Komut: python server.py
Adres: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import jwt
import os
import json
from datetime import datetime
from database import Database
from auth_service import AuthService

app = Flask(__name__)
CORS(app)

# Konfigürasyon
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')
DATABASE_FILE = 'cloud_portfolio.db'

# Servisleri başlat
db = Database(DATABASE_FILE)
auth = AuthService(db, app.config['SECRET_KEY'])

# ============ MIDDLEWARE ============

def token_required(f):
    """Token doğrulama decorator'u"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token gerekli"}), 401
        
        try:
            token = token.replace('Bearer ', '')
            result = auth.verify_token(token)
            
            if not result['success']:
                return jsonify({"error": result.get('error', 'Geçersiz token')}), 401
            
            request.user_id = result['user_id']
            return f(*args, **kwargs)
        
        except Exception as e:
            return jsonify({"error": str(e)}), 401
    
    return decorated

# ============ HEALTH CHECK ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Sunucu sağlık kontrolü"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "HisseTakip Cloud Server"
    }), 200

# ============ AUTH ENDPOINTS ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Yeni kullanıcı kaydı"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({"error": "username, password, email gerekli"}), 400
    
    result = auth.register_user(data['username'], data['email'], data['password'])
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Kullanıcı girişi"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "username ve password gerekli"}), 400
    
    result = auth.login_user(data['username'], data['password'])
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_user_info():
    """Aktif kullanıcı bilgisi"""
    user = auth.get_user_info(request.user_id)
    
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404

@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password():
    """Şifre değiştir"""
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({"error": "old_password ve new_password gerekli"}), 400
    
    result = auth.change_password(request.user_id, data['old_password'], data['new_password'])
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# ============ DATA SYNC ENDPOINTS ============

@app.route('/api/sync/portfolio', methods=['POST'])
@token_required
def sync_portfolio():
    """Portföy verilerini senkronize et"""
    data = request.get_json()
    portfolio_data = data.get('data', [])
    
    try:
        # Mevcut portföyü temizle
        db.clear_all_data(request.user_id)
        
        # Yeni portföyü kaydet
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for item in portfolio_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO portfolios 
                    (user_id, sembol, adet, ort_maliyet, guncel_fiyat)
                    VALUES (?, ?, ?, ?, ?)
                ''', (request.user_id, item['sembol'], item['adet'], 
                      item['ort_maliyet'], item['guncel_fiyat']))
            conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"{len(portfolio_data)} portföy öğesi senkronize edildi"
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/transactions', methods=['POST'])
@token_required
def sync_transactions():
    """İşlem verilerini senkronize et"""
    data = request.get_json()
    transactions = data.get('data', [])
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (request.user_id,))
            
            for trans in transactions:
                cursor.execute('''
                    INSERT INTO transactions 
                    (user_id, sembol, tip, adet, fiyat, toplam, tarih)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (request.user_id, trans['sembol'], trans['tip'],
                      trans['adet'], trans['fiyat'], trans['toplam'], 
                      trans['tarih']))
            conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"{len(transactions)} işlem senkronize edildi"
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/dividends', methods=['POST'])
@token_required
def sync_dividends():
    """Temettü verilerini senkronize et"""
    data = request.get_json()
    dividends = data.get('data', [])
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dividends WHERE user_id = ?", (request.user_id,))
            
            for div in dividends:
                cursor.execute('''
                    INSERT INTO dividends 
                    (user_id, sembol, tutar, adet, hisse_basi_tutar, tarih)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (request.user_id, div['sembol'], div['tutar'],
                      div['adet'], div['hisse_basi_tutar'], div['tarih']))
            conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"{len(dividends)} temettü senkronize edildi"
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/settings', methods=['POST'])
@token_required
def sync_settings():
    """Ayarları senkronize et"""
    data = request.get_json()
    settings = data.get('data', {})
    
    try:
        db.update_settings(settings, request.user_id)
        
        return jsonify({
            "success": True,
            "message": "Ayarlar senkronize edildi"
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============ DATA PULL ENDPOINTS ============

@app.route('/api/pull/portfolio', methods=['GET'])
@token_required
def pull_portfolio():
    """Portföy verilerini indir"""
    try:
        portfolio = db.get_portfolio(request.user_id)
        return jsonify(portfolio), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pull/transactions', methods=['GET'])
@token_required
def pull_transactions():
    """İşlem verilerini indir"""
    try:
        transactions = db.get_transactions(request.user_id)
        return jsonify(transactions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pull/dividends', methods=['GET'])
@token_required
def pull_dividends():
    """Temettü verilerini indir"""
    try:
        dividends = db.get_dividends(request.user_id)
        return jsonify(dividends), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pull/settings', methods=['GET'])
@token_required
def pull_settings():
    """Ayarları indir"""
    try:
        settings = db.get_settings(request.user_id)
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pull/all', methods=['GET'])
@token_required
def pull_all():
    """Tüm verileri indir"""
    try:
        data = {
            "portfolio": db.get_portfolio(request.user_id),
            "transactions": db.get_transactions(request.user_id),
            "dividends": db.get_dividends(request.user_id),
            "settings": db.get_settings(request.user_id)
        }
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint bulunamadı"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Sunucu hatası"}), 500

# ============ MAIN ============

if __name__ == '__main__':
    print("="*60)
    print("📊 HisseTakip Cloud Server başlıyor...")
    print("="*60)
    print("URL: http://localhost:5000")
    print("API Docs: http://localhost:5000/api/health")
    print("\nEndpoints:")
    print("  POST   /api/auth/register")
    print("  POST   /api/auth/login")
    print("  GET    /api/auth/me")
    print("  POST   /api/auth/change-password")
    print("  POST   /api/sync/{portfolio,transactions,dividends,settings}")
    print("  GET    /api/pull/{portfolio,transactions,dividends,settings,all}")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
