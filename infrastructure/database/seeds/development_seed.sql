-- Development Environment Data Seeding
-- This script populates the database with sample data for development

BEGIN;

-- Clear existing data (development only)
TRUNCATE TABLE user_roles, users, roles CASCADE;

-- Reset sequences
ALTER SEQUENCE IF EXISTS users_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS roles_id_seq RESTART WITH 1;

-- Insert development roles
INSERT INTO roles (id, name, description, permissions) VALUES
(uuid_generate_v4(), 'super_admin', 'Super Administrator with all permissions', '{"all": true}'),
(uuid_generate_v4(), 'admin', 'System Administrator', '{"users": {"create": true, "read": true, "update": true, "delete": true}, "blog": {"create": true, "read": true, "update": true, "delete": true}, "comments": {"moderate": true, "delete": true}, "analytics": {"read": true}}'),
(uuid_generate_v4(), 'editor', 'Content Editor', '{"blog": {"create": true, "read": true, "update": true, "delete": true}, "comments": {"moderate": true, "read": true, "update": true}}'),
(uuid_generate_v4(), 'author', 'Content Author', '{"blog": {"create": true, "read": true, "update": "own"}, "comments": {"read": true, "reply": true}}'),
(uuid_generate_v4(), 'moderator', 'Comment Moderator', '{"comments": {"moderate": true, "read": true, "update": true, "delete": true}, "blog": {"read": true}}'),
(uuid_generate_v4(), 'user', 'Regular User', '{"blog": {"read": true}, "comments": {"create": true, "read": true, "update": "own", "delete": "own"}}'),
(uuid_generate_v4(), 'guest', 'Guest User', '{"blog": {"read": true}, "comments": {"read": true}}');

-- Insert development users
INSERT INTO users (id, email, username, password_hash, first_name, last_name, is_active, is_staff, is_superuser, email_verified, phone_number, timezone, language) VALUES
-- Super Admin
(uuid_generate_v4(), 'superadmin@example.com', 'superadmin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Super', 'Admin', true, true, true, true, '+1234567890', 'UTC', 'en'),

-- Admin Users
(uuid_generate_v4(), 'admin@example.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'John', 'Admin', true, true, false, true, '+1234567891', 'UTC', 'en'),
(uuid_generate_v4(), 'jane.admin@example.com', 'jane_admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Jane', 'Administrator', true, true, false, true, '+1234567892', 'America/New_York', 'en'),

-- Editors
(uuid_generate_v4(), 'editor@example.com', 'editor', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Alice', 'Editor', true, false, false, true, '+1234567893', 'Europe/London', 'en'),
(uuid_generate_v4(), 'bob.editor@example.com', 'bob_editor', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Bob', 'Content', true, false, false, true, '+1234567894', 'America/Los_Angeles', 'en'),

-- Authors
(uuid_generate_v4(), 'author1@example.com', 'author1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Charlie', 'Writer', true, false, false, true, '+1234567895', 'UTC', 'en'),
(uuid_generate_v4(), 'author2@example.com', 'author2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Diana', 'Blogger', true, false, false, true, '+1234567896', 'Asia/Tokyo', 'ja'),
(uuid_generate_v4(), 'author3@example.com', 'author3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Eva', 'Journalist', true, false, false, true, '+1234567897', 'Europe/Paris', 'fr'),

-- Moderators
(uuid_generate_v4(), 'moderator@example.com', 'moderator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Frank', 'Moderator', true, false, false, true, '+1234567898', 'UTC', 'en'),

-- Regular Users
(uuid_generate_v4(), 'user1@example.com', 'user1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Grace', 'User', true, false, false, true, '+1234567899', 'UTC', 'en'),
(uuid_generate_v4(), 'user2@example.com', 'user2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Henry', 'Reader', true, false, false, true, '+1234567800', 'America/Chicago', 'en'),
(uuid_generate_v4(), 'user3@example.com', 'user3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Ivy', 'Commenter', true, false, false, false, '+1234567801', 'UTC', 'en'),

-- Test Users (inactive, unverified, etc.)
(uuid_generate_v4(), 'inactive@example.com', 'inactive_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Jack', 'Inactive', false, false, false, false, '+1234567802', 'UTC', 'en'),
(uuid_generate_v4(), 'unverified@example.com', 'unverified_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Kate', 'Unverified', true, false, false, false, '+1234567803', 'UTC', 'en');

-- Assign roles to users
INSERT INTO user_roles (user_id, role_id, assigned_by)
SELECT 
    u.id as user_id,
    r.id as role_id,
    (SELECT id FROM users WHERE username = 'superadmin') as assigned_by
FROM users u
CROSS JOIN roles r
WHERE 
    (u.username = 'superadmin' AND r.name = 'super_admin') OR
    (u.username = 'admin' AND r.name = 'admin') OR
    (u.username = 'jane_admin' AND r.name = 'admin') OR
    (u.username = 'editor' AND r.name = 'editor') OR
    (u.username = 'bob_editor' AND r.name = 'editor') OR
    (u.username = 'author1' AND r.name = 'author') OR
    (u.username = 'author2' AND r.name = 'author') OR
    (u.username = 'author3' AND r.name = 'author') OR
    (u.username = 'moderator' AND r.name = 'moderator') OR
    (u.username IN ('user1', 'user2', 'user3', 'inactive_user', 'unverified_user') AND r.name = 'user');

-- Create some additional test data tables for development
CREATE TABLE IF NOT EXISTS blog_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    author_id UUID NOT NULL REFERENCES users(id),
    category_id UUID REFERENCES blog_categories(id),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    featured BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample blog categories
INSERT INTO blog_categories (name, slug, description) VALUES
('Technology', 'technology', 'Articles about technology trends and innovations'),
('Programming', 'programming', 'Programming tutorials and best practices'),
('Web Development', 'web-development', 'Web development tips and techniques'),
('Database', 'database', 'Database design and optimization'),
('DevOps', 'devops', 'DevOps practices and tools'),
('Security', 'security', 'Cybersecurity and data protection'),
('AI & Machine Learning', 'ai-ml', 'Artificial Intelligence and Machine Learning'),
('Mobile Development', 'mobile-development', 'Mobile app development'),
('Cloud Computing', 'cloud-computing', 'Cloud platforms and services'),
('Open Source', 'open-source', 'Open source projects and contributions');

-- Insert sample blog posts
INSERT INTO blog_posts (title, slug, content, excerpt, author_id, category_id, status, featured, published_at)
SELECT 
    'Getting Started with PostgreSQL Performance Tuning',
    'postgresql-performance-tuning',
    'PostgreSQL is a powerful database system, but like any database, it requires proper tuning to achieve optimal performance. In this comprehensive guide, we''ll explore various techniques to optimize your PostgreSQL database...',
    'Learn essential PostgreSQL performance tuning techniques to optimize your database.',
    (SELECT id FROM users WHERE username = 'author1'),
    (SELECT id FROM blog_categories WHERE slug = 'database'),
    'published',
    true,
    NOW() - INTERVAL '2 days'
UNION ALL
SELECT 
    'Building Scalable Web Applications with Django',
    'scalable-django-applications',
    'Django is an excellent framework for building web applications, but scaling them requires careful consideration of architecture, caching, and database design...',
    'Discover best practices for building scalable Django web applications.',
    (SELECT id FROM users WHERE username = 'author2'),
    (SELECT id FROM blog_categories WHERE slug = 'web-development'),
    'published',
    true,
    NOW() - INTERVAL '5 days'
UNION ALL
SELECT 
    'Introduction to Docker and Containerization',
    'docker-containerization-intro',
    'Docker has revolutionized how we deploy and manage applications. This article provides a comprehensive introduction to Docker and containerization concepts...',
    'A beginner-friendly guide to Docker and containerization.',
    (SELECT id FROM users WHERE username = 'author3'),
    (SELECT id FROM blog_categories WHERE slug = 'devops'),
    'published',
    false,
    NOW() - INTERVAL '1 week'
UNION ALL
SELECT 
    'Advanced React Patterns and Best Practices',
    'advanced-react-patterns',
    'React has evolved significantly over the years. This article explores advanced patterns and best practices for building maintainable React applications...',
    'Explore advanced React patterns for better application architecture.',
    (SELECT id FROM users WHERE username = 'author1'),
    (SELECT id FROM blog_categories WHERE slug = 'programming'),
    'published',
    false,
    NOW() - INTERVAL '10 days'
UNION ALL
SELECT 
    'Securing Your Web Applications: A Complete Guide',
    'web-application-security-guide',
    'Security should be a top priority when developing web applications. This comprehensive guide covers essential security practices and common vulnerabilities...',
    'Essential security practices for web application developers.',
    (SELECT id FROM users WHERE username = 'author2'),
    (SELECT id FROM blog_categories WHERE slug = 'security'),
    'draft',
    false,
    NULL;

-- Add triggers for blog tables
CREATE TRIGGER update_blog_categories_updated_at BEFORE UPDATE ON blog_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add audit triggers for blog tables
CREATE TRIGGER audit_blog_categories AFTER INSERT OR UPDATE OR DELETE ON blog_categories
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

CREATE TRIGGER audit_blog_posts AFTER INSERT OR UPDATE OR DELETE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_category_id ON blog_posts(category_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON blog_posts(published_at);
CREATE INDEX IF NOT EXISTS idx_blog_posts_featured ON blog_posts(featured);
CREATE INDEX IF NOT EXISTS idx_blog_categories_slug ON blog_categories(slug);

COMMIT;

-- Display seeded data summary
SELECT 'Development database seeded successfully!' as message;
SELECT 'Users created: ' || count(*) as users_count FROM users;
SELECT 'Roles created: ' || count(*) as roles_count FROM roles;
SELECT 'Blog categories created: ' || count(*) as categories_count FROM blog_categories;
SELECT 'Blog posts created: ' || count(*) as posts_count FROM blog_posts;