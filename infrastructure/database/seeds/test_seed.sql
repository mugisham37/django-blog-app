-- Test Environment Data Seeding
-- This script creates minimal test data for automated testing

BEGIN;

-- Clear all data for clean test environment
TRUNCATE TABLE user_roles, users, roles CASCADE;

-- Insert test roles
INSERT INTO roles (id, name, description, permissions) VALUES
('11111111-1111-1111-1111-111111111111', 'admin', 'Test Admin', '{"all": true}'),
('22222222-2222-2222-2222-222222222222', 'user', 'Test User', '{"blog": {"read": true}, "comments": {"create": true, "read": true}}');

-- Insert test users with predictable IDs for testing
INSERT INTO users (id, email, username, password_hash, first_name, last_name, is_active, is_staff, is_superuser, email_verified) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'testadmin@test.com', 'testadmin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Test', 'Admin', true, true, true, true),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'testuser@test.com', 'testuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Test', 'User', true, false, false, true),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'inactive@test.com', 'inactiveuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VJWZp/k/K', 'Inactive', 'User', false, false, false, false);

-- Assign roles to test users
INSERT INTO user_roles (user_id, role_id, assigned_by) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa');

-- Create test blog categories
CREATE TABLE IF NOT EXISTS blog_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO blog_categories (id, name, slug, description) VALUES
('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Test Category', 'test-category', 'Category for testing');

-- Create test blog posts
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

INSERT INTO blog_posts (id, title, slug, content, excerpt, author_id, category_id, status, published_at) VALUES
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'Test Blog Post', 'test-blog-post', 'This is a test blog post content.', 'Test excerpt', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'published', NOW()),
('ffffffff-ffff-ffff-ffff-ffffffffffff', 'Draft Post', 'draft-post', 'This is a draft post.', 'Draft excerpt', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'draft', NULL);

-- Add triggers for test tables
CREATE TRIGGER update_blog_categories_updated_at BEFORE UPDATE ON blog_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create test app settings
CREATE TABLE IF NOT EXISTS app_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO app_settings (key, value, description) VALUES
('test_setting', '"test_value"', 'A test setting for automated tests'),
('posts_per_page', '5', 'Test posts per page setting');

-- Create indexes for test performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_category_id ON blog_posts(category_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);

COMMIT;

-- Display test seeding summary
SELECT 'Test database seeded successfully!' as message;
SELECT 'Test users created: ' || count(*) as users_count FROM users;
SELECT 'Test roles created: ' || count(*) as roles_count FROM roles;
SELECT 'Test blog posts created: ' || count(*) as posts_count FROM blog_posts;