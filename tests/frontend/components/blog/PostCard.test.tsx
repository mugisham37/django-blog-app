/**
 * Blog post card component tests
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PostCard } from "../../../../apps/web/src/components/blog/PostCard";

const mockPost = {
  id: 1,
  title: "Test Blog Post",
  slug: "test-blog-post",
  content:
    "This is a test blog post content that should be truncated in the card view.",
  excerpt: "This is a test blog post content...",
  author: {
    username: "testauthor",
    first_name: "Test",
    last_name: "Author",
  },
  category: {
    name: "Technology",
    slug: "technology",
  },
  tags: [
    { name: "JavaScript", slug: "javascript" },
    { name: "React", slug: "react" },
  ],
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:00:00Z",
  featured_image: "/images/test-post.jpg",
  is_featured: false,
  read_time: 5,
};

// Mock Next.js router
const mockPush = jest.fn();
jest.mock("next/router", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe("PostCard", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders post information correctly", () => {
    render(<PostCard post={mockPost} />);

    expect(screen.getByText("Test Blog Post")).toBeInTheDocument();
    expect(
      screen.getByText(/this is a test blog post content/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Test Author")).toBeInTheDocument();
    expect(screen.getByText("Technology")).toBeInTheDocument();
    expect(screen.getByText("5 min read")).toBeInTheDocument();
  });

  it("displays tags correctly", () => {
    render(<PostCard post={mockPost} />);

    expect(screen.getByText("JavaScript")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("shows featured badge for featured posts", () => {
    const featuredPost = { ...mockPost, is_featured: true };
    render(<PostCard post={featuredPost} />);

    expect(screen.getByText("Featured")).toBeInTheDocument();
  });

  it("navigates to post detail on click", async () => {
    const user = userEvent.setup();
    render(<PostCard post={mockPost} />);

    const postCard = screen.getByRole("article");
    await user.click(postCard);

    expect(mockPush).toHaveBeenCalledWith("/blog/test-blog-post");
  });

  it("navigates to post detail on title click", async () => {
    const user = userEvent.setup();
    render(<PostCard post={mockPost} />);

    const titleLink = screen.getByRole("link", { name: "Test Blog Post" });
    await user.click(titleLink);

    expect(mockPush).toHaveBeenCalledWith("/blog/test-blog-post");
  });

  it("navigates to category page on category click", async () => {
    const user = userEvent.setup();
    render(<PostCard post={mockPost} />);

    const categoryLink = screen.getByRole("link", { name: "Technology" });
    await user.click(categoryLink);

    expect(mockPush).toHaveBeenCalledWith("/blog/category/technology");
  });

  it("navigates to tag page on tag click", async () => {
    const user = userEvent.setup();
    render(<PostCard post={mockPost} />);

    const tagLink = screen.getByRole("link", { name: "JavaScript" });
    await user.click(tagLink);

    expect(mockPush).toHaveBeenCalledWith("/blog/tag/javascript");
  });

  it("displays formatted date", () => {
    render(<PostCard post={mockPost} />);

    expect(screen.getByText("Jan 1, 2023")).toBeInTheDocument();
  });

  it("handles missing featured image gracefully", () => {
    const postWithoutImage = { ...mockPost, featured_image: null };
    render(<PostCard post={postWithoutImage} />);

    // Should render without errors and show placeholder
    expect(screen.getByRole("article")).toBeInTheDocument();
  });

  it("truncates long content appropriately", () => {
    const longContentPost = {
      ...mockPost,
      content:
        "This is a very long blog post content that should be truncated when displayed in the card view to maintain consistent layout and readability across all post cards.",
      excerpt:
        "This is a very long blog post content that should be truncated...",
    };

    render(<PostCard post={longContentPost} />);

    const content = screen.getByText(/this is a very long blog post content/i);
    expect(content.textContent).toContain("...");
  });

  it("has proper accessibility attributes", () => {
    render(<PostCard post={mockPost} />);

    const article = screen.getByRole("article");
    expect(article).toHaveAttribute("aria-label", "Blog post: Test Blog Post");

    const titleLink = screen.getByRole("link", { name: "Test Blog Post" });
    expect(titleLink).toHaveAttribute("aria-describedby");
  });

  it("supports keyboard navigation", async () => {
    const user = userEvent.setup();
    render(<PostCard post={mockPost} />);

    const titleLink = screen.getByRole("link", { name: "Test Blog Post" });

    // Tab to the link and press Enter
    await user.tab();
    expect(titleLink).toHaveFocus();

    await user.keyboard("{Enter}");
    expect(mockPush).toHaveBeenCalledWith("/blog/test-blog-post");
  });
});
