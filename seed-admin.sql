-- Seed default admin user
-- Username: Admin
-- Password: admin123

INSERT INTO shared.users (username, email, password_hash, role, is_active)
VALUES (
    'Admin',
    'admin@netnynja.local',
    '$argon2id$v=19$m=65536,t=3,p=4$FUHIbYhlF0fAmDkKKrwx1w$223Jm8aGdTeNTEnKR/shIuhw7tqeADcUIxSJtMoVkhU',
    'admin',
    true
)
ON CONFLICT (username) DO UPDATE SET
    password_hash = '$argon2id$v=19$m=65536,t=3,p=4$FUHIbYhlF0fAmDkKKrwx1w$223Jm8aGdTeNTEnKR/shIuhw7tqeADcUIxSJtMoVkhU',
    role = 'admin',
    is_active = true;
