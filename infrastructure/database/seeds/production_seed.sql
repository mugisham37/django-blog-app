-- Production Environment Data Seeding
-- This script creates minimal essential data for production

BEGIN;

-- Insert production roles (only essential ones)
INSERT INTO roles (name, description, permissions) VALUES
('admin', 'System Administrator', '{"users": {"create": true, "read": true, "update": true, "delete": true}, "blog": {"create": true, "read": true, "update": true, "delete": true}, "comments": {"moderate": true, "delete": true}, "analytics": {"read": true}}'),
('editor', 'Content Editor', '{"blog": {"create": true, "read": true, "update": true, "delete": true}, "comments": {"moderate": true, "read": true, "update": true}}'),
('author', 'Content Author', '{"blog": {"create": true, "read": true, "update": "own"}, "comments": {"read": true, "reply": true}}'),
('moderator', 'Comment Moderator', '{"comments": {"moderate": true, "read": true, "update": true, "delete": true}, "blog": {"read": true}}'),
('user', 'Regular User', '{"blog": {"read": true}, "comments": {"create": true, "read": true, "update": "own", "delete": "own"}}')
ON CONFLICT (name) DO NOTHING;

-- Create essential blog categories for production
CREATE TABLE IF NOT EXISTS blog_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO blog_categories (name, slug, description) VALUES
('General', 'general', 'General blog posts and announcements'),
('News', 'news', 'Company and industry news'),
('Updates', 'updates', 'Product updates and releases')
ON CONFLICT (slug) DO NOTHING;

-- Create blog posts table
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

-- Add triggers for production tables
CREATE TRIGGER update_blog_categories_updated_at BEFORE UPDATE ON blog_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add audit triggers
CREATE TRIGGER audit_blog_categories AFTER INSERT OR UPDATE OR DELETE ON blog_categories
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

CREATE TRIGGER audit_blog_posts AFTER INSERT OR UPDATE OR DELETE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_category_id ON blog_posts(category_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON blog_posts(published_at);
CREATE INDEX IF NOT EXISTS idx_blog_posts_featured ON blog_posts(featured);
CREATE INDEX IF NOT EXISTS idx_blog_categories_slug ON blog_categories(slug);

-- Create application settings table
CREATE TABLE IF NOT EXISTS app_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default application settings
INSERT INTO app_settings (key, value, description) VALUES
('site_name', '"Enterprise Blog"', 'Website name displayed in headers and titles'),
('site_description', '"A modern enterprise blog platform"', 'Website description for SEO'),
('posts_per_page', '10', 'Number of blog posts to display per page'),
('allow_comments', 'true', 'Whether to allow comments on blog posts'),
('require_approval', 'true', 'Whether comments require approval before publishing'),
('maintenance_mode', 'false', 'Enable maintenance mode to disable public access'),
('registration_enabled', 'true', 'Allow new user registrations'),
('email_verification_required', 'true', 'Require email verification for new accounts')
ON CONFLICT (key) DO NOTHING;

-- Add trigger for app_settings
CREATE TRIGGER update_app_settings_updated_at BEFORE UPDATE ON app_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER audit_app_settings AFTER INSERT OR UPDATE OR DELETE ON app_settings
    FOR EACH ROW EXECUTE FUNCTION audit.audit_trigger();

COMMIT;

-- Display production seeding summary
SELECT 'Production database seeded successfully!' as message;
SELECT 'Essential roles created: ' || count(*) as roles_count FROM roles;
SELECT 'Blog categories created: ' || count(*) as categories_count FROM blog_categories;
SELECT 'Application settings created: ' || count(*) as settings_count FROM app_settings;