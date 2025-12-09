# 📸 ImageUP - Geolocation Image Upload System

A Flask-based web application for uploading images with geolocation data, featuring role-based authentication with user and admin capabilities.

## ✨ Features

### Authentication & Authorization
- **User Registration & Login** - Secure password hashing with role selection
- **Two User Roles:**
  - **User**: Can upload images with geolocation data
  - **Admin**: Full access including user management and upload oversight
- **Session-based Authentication** - Secure session management

### Image Upload
- Upload images with automatic geolocation capture
- Store images as binary data in SQLite database
- Track latitude and longitude coordinates
- Associate uploads with user accounts

### Admin Dashboard
- View all uploaded images with user information
- Manage users (view, delete)
- Delete any upload
- View statistics (total uploads, total users)

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the repository**
   ```bash
   cd ImageUP
   ```

2. **Install required packages**
   ```bash
   pip install flask werkzeug
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
ImageUP/
│
├── app.py                      # Main Flask application
├── uploads.db                  # SQLite database (auto-created)
├── db_check.py                 # Database utility script
├── README.md                   # This file
│
└── templates/
    ├── index.html              # Main upload page
    ├── login.html              # Login page
    ├── register.html           # Registration page
    └── admin_dashboard.html    # Admin management panel
```

## 🔐 Authentication System

### Registration
1. Navigate to `/register`
2. Choose a username and password
3. Select role (User or Admin)
4. Submit to create account

### Login
1. Navigate to `/login` (or go to `/` which redirects if not logged in)
2. Enter credentials
3. Access granted based on role

## 👤 User Roles

### User Role
- Upload images with geolocation
- View own upload interface
- Logout functionality

### Admin Role
- All user capabilities
- Access to Admin Dashboard
- View all uploads from all users
- Delete any upload
- View all registered users
- Delete users (except self)

## 🛠️ API Endpoints

### Public Routes
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /register` - Registration page
- `POST /register` - Create new user
- `GET /logout` - Logout current user

### Protected Routes (Login Required)
- `GET /` - Main upload page
- `POST /upload` - Upload image with geolocation

### Admin Routes (Admin Role Required)
- `GET /admin/dashboard` - Admin management panel
- `POST /admin/delete_upload/<id>` - Delete specific upload
- `POST /admin/delete_user/<id>` - Delete specific user

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT
)
```

### Uploads Table
```sql
CREATE TABLE uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    content_type TEXT,
    image BLOB,
    latitude REAL,
    longitude REAL,
    created_at TEXT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

## 🔧 Configuration

### Secret Key
**Important**: Change the secret key in `app.py` for production use:
```python
app.secret_key = 'your-secret-key-change-this-in-production'
```

### Database Path
Default database location:
```python
DB_PATH = "uploads.db"
```

## 📱 Usage Guide

### Uploading Images

1. **Login** to your account
2. **Click "Get My Location"** to capture geolocation coordinates
3. **Select an image** file from your device
4. **Click "Upload Image"** to submit

### Admin Functions

1. **Access Dashboard** by clicking "Admin Dashboard" button (admin users only)
2. **View Statistics** - See total uploads and users
3. **Manage Uploads** - View all uploads with details, delete as needed
4. **Manage Users** - View all users, delete users (cannot delete yourself)

## 🔒 Security Features

- **Password Hashing**: Using Werkzeug's secure password hashing
- **Session Management**: Flask sessions with secret key
- **Role-Based Access Control**: Decorators enforce permissions
- **SQL Injection Prevention**: Parameterized queries
- **CSRF Protection**: Form-based authentication

## 🐛 Troubleshooting

### Database Locked Error
If you see "database is locked" error:
```powershell
# Stop all Python processes
Stop-Process -Name python -Force

# Or delete and recreate database
Remove-Item uploads.db
python app.py
```

### Missing Column Error
The application automatically migrates the database schema. If issues persist:
```powershell
Remove-Item uploads.db
python app.py
```

### Port Already in Use
Change the port in `app.py`:
```python
app.run(debug=True, port=5001)
```

## 🚧 Development

### Debug Mode
Debug mode is enabled by default in `app.py`:
```python
app.run(debug=True)
```

For production, set to `False` and use a production WSGI server.

## 📝 Future Enhancements

- [ ] Image viewing/display functionality
- [ ] User profile pages
- [ ] Image gallery view
- [ ] Export data functionality
- [ ] Email verification
- [ ] Password reset functionality
- [ ] Image thumbnails
- [ ] Search and filter capabilities
- [ ] Rate limiting
- [ ] File type validation

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Support

For issues or questions, please check:
1. This README
2. Error messages in the Flask console
3. Browser developer console for frontend issues

---

**Built with Flask** 🐍 | **Powered by SQLite** 💾 | **Secured with Werkzeug** 🔐
