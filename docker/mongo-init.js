// On se place sur la base applicative
db = db.getSiblingDB("medical_db");

// Utilisateur "admin_app" : admin applicatif sur la base medical_db
db.createUser({
  user: "admin_app",
  pwd: "AdminAppPassword123!",
  roles: [
    { role: "dbOwner", db: "medical_db" }
  ]
});

// Utilisateur "app_user" : lecture/écriture sur medical_db
db.createUser({
  user: "app_user",
  pwd: "app_password",
  roles: [
    { role: "readWrite", db: "medical_db" }
  ]
});

// Utilisateur "data_analyst" : lecture seule pour les analystes
db.createUser({
  user: "data_analyst",
  pwd: "AnalystPassword123!",
  roles: [
    { role: "read", db: "medical_db" }
  ]
});

