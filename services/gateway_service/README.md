# QuickQuiz Gateway Service

Clean, production-ready Django API Gateway for QuickQuiz microservices architecture.

## 🏗️ Architecture

```
Frontend Applications
        ↓
Django Gateway Service (Port 8001)
        ↓
┌─────────────────┬─────────────────┐
│                 │                 │
Quiz Generator   Quiz Evaluator   Future Services
(Port 8003)      (Port 8005)      (Port 80XX)
```

## 📂 Project Structure

```
services/gateway_service/
├── manage.py                    # Django management
├── requirements.txt            # Dependencies
├── gateway/                    # Django project
│   ├── settings.py            # Enhanced configuration
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI config
│   └── asgi.py                # ASGI config
├── api/                       # API application
│   ├── service_clients.py     # Enhanced HTTP clients
│   ├── views.py              # API endpoints
│   ├── urls.py               # API routing
│   └── models.py             # Data models (future)
├── data/                      # Database files
├── logs/                      # Log files
├── static/                    # Static files
└── templates/                 # HTML templates
```

## 🚀 Quick Start

### 1. Navigate to Gateway Service

```bash
cd services/gateway_service
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Start Gateway Service

```bash
python manage.py runserver 8001
```

## 🔧 Configuration

### Environment Variables (.env in project root)

```env
# Gateway Configuration
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Microservices
QUIZ_GENERATOR_HOST=localhost
QUIZ_GENERATOR_PORT=8003
QUIZ_EVALUATOR_HOST=localhost
QUIZ_EVALUATOR_PORT=8005
```

### Key Features

- ✅ **Enhanced Error Handling** - Comprehensive error responses
- ✅ **Retry Logic** - Automatic retry for failed requests
- ✅ **Health Monitoring** - Service health tracking
- ✅ **Request Logging** - Detailed request/response logging
- ✅ **Performance Metrics** - Response time tracking
- ✅ **CORS Support** - Frontend integration ready
- ✅ **Clean Architecture** - Proper Django structure

## 📡 API Endpoints

### Gateway Information

```http
GET /
```

### Health Check

```http
GET /api/health/
```

### Generate Quiz

```http
POST /api/quiz/generate/
```

### Evaluate Quiz

```http
POST /api/quiz/evaluate/
```

### Grading Scale

```http
GET /api/quiz/grading-scale/
```

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8001/api/health/
```

### Generate Quiz

```bash
curl -X POST http://localhost:8001/api/quiz/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "sections": [{"id": "test", "summary": "Python basics"}],
    "config": {"n_questions": 3}
  }'
```

## 📊 Monitoring

### Service Health

- Individual service health checks
- Response time monitoring
- Error rate tracking
- Automatic service discovery

### Logging

- Request/response logging
- Error tracking
- Performance metrics
- Service communication logs

## 🔒 Security

- CSRF protection
- CORS configuration
- Input validation
- Error sanitization
- Rate limiting (future)

## 🚀 Production Deployment

### Using Gunicorn

```bash
gunicorn gateway.wsgi:application --bind 0.0.0.0:8001
```

### Using Docker (future)

```bash
docker build -t quickquiz-gateway .
docker run -p 8001:8001 quickquiz-gateway
```

## 📈 Performance

- Connection pooling
- Request timeout configuration
- Retry strategy
- Response caching (future)
- Load balancing ready

## 🛠️ Development

### Adding New Services

1. Update `MICROSERVICES` in `settings.py`
2. Create service client in `service_clients.py`
3. Add API endpoints in `views.py`
4. Update URL routing

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
flake8 .
black .
isort .
```

## 📞 Troubleshooting

### Common Issues

1. **Service Connection Failed**

   - Check if microservices are running
   - Verify host/port configuration
   - Check network connectivity

2. **Database Issues**

   - Run migrations: `python manage.py migrate`
   - Check database permissions

3. **Import Errors**
   - Verify virtual environment activation
   - Check Python path
   - Install missing dependencies

### Logs Location

- Console logs: Real-time in terminal
- File logs: `logs/gateway.log`
- Django logs: Follow Django configuration

## 🔄 Migration from Old Structure

If migrating from the old structure:

1. Stop old Django server
2. Copy data from old `db.sqlite3` to `data/gateway.db`
3. Update frontend API endpoints from `:8000` to `:8001`
4. Test all endpoints

## 📋 TODO

- [ ] API documentation with drf-spectacular
- [ ] Rate limiting implementation
- [ ] Caching layer
- [ ] Authentication/Authorization
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring dashboard
