# BW-MetaBase

A partial replication of Beachwood's PowerBI system using Python and Metabase for data visualization and analytics.

## Overview

BW-MetaBase is a modern data analytics platform that replicates key functionality from Beachwood's PowerBI system. The solution leverages Python for data processing, Metabase for visualization, and implements a secure multi-tenant architecture with user-store relationships.

## Architecture

### Core Components
- **Data Sources**: OneDrive and Microsoft Dataverse
- **Backend**: Python-based data processing and API services
- **Visualization**: Metabase dashboard platform
- **Infrastructure**: Docker containers with reverse proxy
- **Authentication**: User-based access control with store-level permissions

### Server Infrastructure
- **Production Server**: 83.229.35.162
- **Container Architecture**: 
  - Main application container
  - Reverse proxy container (for HTTPS/443 access)
- **Environments**: Staging and Production

## Features

### Data Integration
- **OneDrive Integration**: Automated data extraction from OneDrive storage
- **Dataverse Connection**: Real-time data synchronization with Microsoft Dataverse
- **Python ETL Pipeline**: Robust data transformation and loading processes

### User Management & Security
- **Authentication System**: Secure login for Metabase access
- **Role-Based Access**: Users can only access stores they're associated with
- **Multi-Tenant Architecture**: Store-level data isolation

### Data Visualization
- **Metabase Dashboards**: Interactive business intelligence dashboards
- **Store-Specific Views**: Customized dashboards per store/user relationship
- **Real-Time Analytics**: Up-to-date business metrics and KPIs

## Project Structure

```
BW-MetaBase/
├── docker/
│   ├── app/
│   │   └── Dockerfile
│   ├── reverse-proxy/
│   │   └── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── data/
│   │   ├── extractors/
│   │   ├── transformers/
│   │   └── loaders/
│   ├── api/
│   ├── auth/
│   └── utils/
├── config/
│   ├── staging/
│   └── production/
├── scripts/
├── tests/
└── docs/
```

## Technology Stack

### Backend
- **Python 3.9+**: Core programming language
- **FastAPI**: REST API framework
- **Pandas**: Data manipulation and analysis
- **SQLAlchemy**: Database ORM
- **Celery**: Asynchronous task processing

### Data & Visualization
- **Metabase**: Business intelligence and visualization
- **PostgreSQL**: Primary database
- **Redis**: Caching and session management

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Reverse proxy
- **Let's Encrypt**: SSL certificates
- **Docker Compose**: Multi-container orchestration

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.9 or higher
- Access to OneDrive and Dataverse APIs
- SSL certificates for HTTPS

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/PTPSystem/BW-MetaBase.git
   cd BW-MetaBase
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and run with Docker**
   ```bash
   docker-compose up -d
   ```

### Configuration

#### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@db:5432/bw_metabase
REDIS_URL=redis://redis:6379

# OneDrive API
ONEDRIVE_CLIENT_ID=your_client_id
ONEDRIVE_CLIENT_SECRET=your_client_secret
ONEDRIVE_TENANT_ID=your_tenant_id

# Dataverse API
DATAVERSE_URL=https://your-org.crm.dynamics.com
DATAVERSE_CLIENT_ID=your_dataverse_client_id
DATAVERSE_CLIENT_SECRET=your_dataverse_client_secret

# Metabase
METABASE_SECRET_KEY=your_secret_key
METABASE_DATABASE_URL=postgresql://user:password@db:5432/metabase

# Security
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

## Deployment

### Staging Environment
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production Environment
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Reverse Proxy Setup
The reverse proxy container handles:
- SSL termination
- Load balancing
- Multiple container routing on port 443

## Data Flow

1. **Data Extraction**: Python scripts pull data from OneDrive and Dataverse
2. **Data Transformation**: ETL processes clean and structure the data
3. **Data Loading**: Processed data is stored in PostgreSQL
4. **User Authentication**: Users authenticate through the custom auth system
5. **Store Authorization**: Access is restricted based on user-store relationships
6. **Visualization**: Metabase displays store-specific dashboards

## User & Store Relationship Model

```sql
Users
├── user_id (Primary Key)
├── username
├── email
├── password_hash
└── created_at

Stores
├── store_id (Primary Key)
├── store_name
├── location
└── created_at

UserStoreAccess
├── user_id (Foreign Key)
├── store_id (Foreign Key)
├── access_level
└── granted_at
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/profile` - Get user profile

### Data Management
- `GET /api/stores` - Get user's accessible stores
- `GET /api/stores/{store_id}/data` - Get store-specific data
- `POST /api/data/sync` - Trigger data synchronization

### Admin
- `POST /api/admin/users` - Create user
- `POST /api/admin/access` - Grant store access

## Monitoring & Maintenance

### Health Checks
- Application health: `GET /health`
- Database connectivity: `GET /health/db`
- External API status: `GET /health/apis`

### Logging
- Application logs: `/var/log/bw-metabase/app.log`
- Access logs: `/var/log/bw-metabase/access.log`
- Error logs: `/var/log/bw-metabase/error.log`

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Linting
flake8 src/
black src/

# Type checking
mypy src/
```

### Database Migrations
```bash
alembic upgrade head
```

## Security Considerations

- All API communications use HTTPS
- JWT tokens for session management
- Password hashing with bcrypt
- Store-level data isolation
- Regular security audits and updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is proprietary and confidential. All rights reserved.

## Support

For technical support or questions, please contact:
- **Development Team**: dev@beachwood.com
- **Infrastructure**: ops@beachwood.com

## Roadmap

### Phase 1 (Current)
- [x] Basic Docker setup
- [x] OneDrive integration
- [x] User authentication
- [ ] Store relationship model
- [ ] Metabase integration

### Phase 2
- [ ] Advanced analytics
- [ ] Real-time dashboards
- [ ] Mobile responsiveness
- [ ] Performance optimization

### Phase 3
- [ ] Machine learning insights
- [ ] Automated reporting
- [ ] Advanced user management
- [ ] Multi-language support

## Implementation Plan

### Phase 1: Foundation & Infrastructure

#### 1.1 Docker Setup for Metabase
**Priority**: High | **Timeline**: 1-2 weeks

**Tasks**:
- Create Metabase Docker container with PostgreSQL backend
- Configure sample data integration from existing ETL patterns
- Set up persistent volumes for data and configurations
- Configure environment variables for database connections

**Sample Data Sources**:
- Store performance metrics
- Labor forecast data (following existing labor_forecast.py patterns)
- Sales forecast data (following existing sales_forecast.py patterns)
- Sample user-store relationship data

**Docker Structure**:
```
docker/
├── metabase/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── sample-data/
├── database/
│   └── init-scripts/
└── volumes/
```

#### 1.2 SSL Security Implementation
**Priority**: High | **Timeline**: 1 week

**Tasks**:
- Obtain SSL certificates for StoreMgnt.Beachwood.me
- Configure Let's Encrypt for automatic renewal
- Set up certificate management scripts
- Implement HTTPS redirects

#### 1.3 Nginx Reverse Proxy Container
**Priority**: High | **Timeline**: 1 week

**Tasks**:
- Create dedicated Nginx Docker container
- Configure multi-domain SSL support
- Set up routing for existing str.ptpsystem.com
- Add routing for StoreMgnt.Beachwood.me → Metabase
- Implement load balancing and health checks

**Nginx Configuration**:
```nginx
# Handle multiple SSL sites
server {
    listen 443 ssl http2;
    server_name str.ptpsystem.com;
    # Existing configuration
}

server {
    listen 443 ssl http2;
    server_name StoreMgnt.Beachwood.me;
    location / {
        proxy_pass http://metabase:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Phase 2: ETL Architecture Development

#### 2.1 ETL Structure Design
**Priority**: High | **Timeline**: 2-3 weeks

Based on the existing Beachwood-Data-Integration repository analysis, implement:

**Core ETL Components** (following existing patterns):

```python
src/
├── etl/
│   ├── extractors/
│   │   ├── onedrive_extractor.py      # New: OneDrive API integration
│   │   ├── dataverse_extractor.py     # New: Dataverse API integration  
│   │   ├── labor_extractor.py         # Adapted from labor_processing.py
│   │   └── sales_extractor.py         # Adapted from sales_forecast.py
│   ├── transformers/
│   │   ├── data_cleaner.py
│   │   ├── store_transformer.py
│   │   ├── labor_transformer.py       # From existing labor patterns
│   │   └── sales_transformer.py       # From existing sales patterns
│   ├── loaders/
│   │   ├── metabase_loader.py
│   │   ├── postgresql_loader.py
│   │   └── dataverse_loader.py        # Reuse existing Dataverse integration
│   └── orchestration/
│       ├── pipeline_manager.py        # Based on main.py patterns
│       ├── scheduler.py
│       └── monitoring.py              # Based on email summary patterns
```

**Key Adaptations from Existing Code**:

1. **Labor Data Processing**: 
   - Reuse labor_processing.py patterns for employee data
   - Adapt labor_forecast.py for Metabase visualization
   - Maintain existing batch processing capabilities

2. **Sales Forecasting**:
   - Leverage existing ARIMA/SARIMA models from sales_forecast.py
   - Adapt day-part breakdown logic for Metabase dashboards
   - Reuse Dataverse integration patterns

3. **Email Notifications**:
   - Adapt existing send_summary_email() function
   - Maintain Microsoft Graph API integration
   - Add ETL pipeline status reporting

#### 2.2 OneDrive Integration
**Priority**: Medium | **Timeline**: 2 weeks

**Implementation**:
- Microsoft Graph API integration for file access
- Automated file discovery and download
- Data validation and error handling
- Integration with existing file processing patterns

**Example Structure** (based on existing patterns):
```python
class OneDriveExtractor:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
    def get_file_list(self):
        # Similar to existing get_file_list() in labor_processing.py
        pass
        
    def download_files(self, files):
        # Adapt existing download_files() pattern
        pass
```

#### 2.3 Dataverse Integration
**Priority**: Medium | **Timeline**: 1 week

**Reuse Existing Components**:
- Leverage existing Dataverse authentication from labor_forecast.py
- Adapt batch upsert operations from sales_forecast.py
- Reuse error handling and retry logic

### Phase 3: User Authentication & Authorization

#### 3.1 Metabase Authentication System
**Priority**: High | **Timeline**: 2 weeks

**Implementation**:
- Custom authentication provider for Metabase
- Integration with existing user management
- SSO configuration if needed
- Session management and security

#### 3.2 User-Store Relationship Model
**Priority**: High | **Timeline**: 1 week

**Database Schema**:
```sql
-- Based on existing store management patterns
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stores (
    store_id VARCHAR(10) PRIMARY KEY,  -- Matching existing 6-digit format
    store_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_store_access (
    user_id INTEGER REFERENCES users(user_id),
    store_id VARCHAR(10) REFERENCES stores(store_id),
    access_level VARCHAR(50) DEFAULT 'read',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, store_id)
);
```

### Phase 4: Integration & Testing

#### 4.1 End-to-End Testing
**Priority**: High | **Timeline**: 1 week

**Test Scenarios**:
- ETL pipeline execution with sample data
- User authentication and store access control
- Dashboard rendering with filtered data
- SSL certificate validation
- Docker container orchestration

#### 4.2 Performance Optimization
**Priority**: Medium | **Timeline**: 1 week

**Areas**:
- Database query optimization
- Metabase dashboard caching
- Docker resource allocation
- Nginx performance tuning

## Implementation Feedback & Recommendations

### ✅ Strengths of Current Plan

1. **Leveraging Existing Code**: Excellent reuse of proven ETL patterns from Beachwood-Data-Integration
2. **Proven Architecture**: Following successful patterns from labor_processing.py and sales_forecast.py
3. **Scalable Infrastructure**: Docker-based approach supports easy scaling
4. **Security Focus**: SSL and user authentication prioritized

### ⚠️ Areas for Consideration

1. **Data Synchronization**: 
   - **Recommendation**: Implement real-time sync for critical data
   - **Suggestion**: Use existing batch processing patterns but add incremental updates

2. **Backup Strategy**: 
   - **Missing**: Database backup and disaster recovery plan
   - **Recommendation**: Implement automated backups for both PostgreSQL and Metabase configs

3. **Monitoring & Alerting**:
   - **Enhancement**: Extend existing email notification system
   - **Suggestion**: Add health checks and automated failover

4. **Performance Considerations**:
   - **Concern**: Large datasets may impact Metabase performance
   - **Recommendation**: Implement data partitioning and archiving strategy

### 🚀 Enhancement Suggestions

1. **Gradual Migration**:
   - Start with a subset of stores for initial testing
   - Gradually migrate from PowerBI to MetaBase

2. **Data Quality Assurance**:
   - Implement data validation rules based on existing patterns
   - Add data quality dashboards

3. **User Training & Documentation**:
   - Create user guides for MetaBase transition
   - Document differences from PowerBI workflows

4. **API Integration**:
   - Expose REST APIs for external integrations
   - Follow existing Dataverse integration patterns

### 📋 Detailed Next Steps

1. **Week 1-2**: Set up development environment and basic Docker containers
2. **Week 3-4**: Implement ETL foundation using existing code patterns  
3. **Week 5-6**: Configure Nginx, SSL, and authentication
4. **Week 7-8**: User-store relationship implementation and testing
5. **Week 9-10**: Performance optimization and production deployment

### 💡 Technical Recommendations

1. **Use Docker Compose**: Orchestrate all containers (Metabase, PostgreSQL, Nginx, ETL)
2. **Environment Variables**: Centralize configuration management
3. **Health Checks**: Implement container health monitoring
4. **Log Aggregation**: Centralize logging from all containers
5. **Secrets Management**: Use Docker secrets for sensitive data

---

**Last Updated**: August 24, 2025
**Version**: 1.0.0
