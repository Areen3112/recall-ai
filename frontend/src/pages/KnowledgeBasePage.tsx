import { useState } from 'react';
import type React from 'react';
import {
  Plus,
  Database,
  CheckCircle2,
  Info
} from 'lucide-react';
import { MOCK_KNOWLEDGE_ARTICLES } from '../data/mock/knowledgeBase';
import type { KnowledgeArticle } from '../types';
import { SearchInput } from '../components/ui/SearchInput';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { MarkdownRenderer } from '../components/ui/MarkdownRenderer';

export const KnowledgeBasePage: React.FC = () => {
  const [articles, setArticles] = useState<KnowledgeArticle[]>(MOCK_KNOWLEDGE_ARTICLES);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedArticle, setSelectedArticle] = useState<KnowledgeArticle | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // New Article Form state
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState<KnowledgeArticle['category']>('Troubleshooting');
  const [newExcerpt, setNewExcerpt] = useState('');
  const [newContent, setNewContent] = useState('');

  const categories = [
    'all',
    'Audio & Connectivity',
    'Hardware',
    'Troubleshooting',
    'Policies',
  ];

  const filteredArticles = articles.filter((art) => {
    const matchesCategory =
      selectedCategory === 'all' || art.category === selectedCategory;
    const matchesSearch =
      art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const handleCreateArticle = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const created: KnowledgeArticle = {
      id: `kb-${Date.now()}`,
      title: newTitle,
      slug: newTitle.toLowerCase().replace(/\s+/g, '-'),
      category: newCategory,
      excerpt: newExcerpt || 'Demonstration troubleshooting article.',
      content: newContent || 'Article content details...',
      lastUpdated: 'Just now',
      readTime: '2 min read',
      indexedInHindsight: true,
      tags: ['Demo', newCategory],
    };

    setArticles([created, ...articles]);
    setIsCreateModalOpen(false);
    setNewTitle('');
    setNewExcerpt('');
    setNewContent('');
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-[#F4F4F7] tracking-tight">
              Knowledge Base Management
            </h1>
            <Badge variant="violet" size="sm">
              Demonstration Library
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-[#92929F] mt-1">
            Standard operating procedures and device-scoped diagnostic articles designed for Hindsight long-term memory ingestion.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsCreateModalOpen(true)}
          icon={<Plus className="w-4 h-4" />}
        >
          Create Article
        </Button>
      </div>

      {/* Demo notice banner */}
      <div className="p-3 rounded-xl bg-[#12121A] border border-white/[0.06] flex items-center justify-between text-xs text-[#92929F]">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-[#9B8CFF] shrink-0" />
          <span>
            Demonstration library: Diagnostic steps distinguish device-specific actions (e.g. Apex Pro reset) from host platform commands.
          </span>
        </div>
        <span className="font-mono text-[11px] text-[#626270]">Demo Store</span>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#12121A] p-3 rounded-xl border border-white/[0.06]">
        {/* Category Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-[#191923] text-[#F4F4F7] border border-white/[0.08] shadow-sm'
                  : 'text-[#92929F] hover:text-[#F4F4F7]'
              }`}
            >
              {cat === 'all' ? 'All Categories' : cat}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="w-full sm:w-72">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search documentation, codes..."
          />
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        {filteredArticles.map((article) => (
          <div
            key={article.id}
            onClick={() => setSelectedArticle(article)}
            className="p-5 rounded-2xl bg-[#12121A] border border-white/[0.07] hover:border-[#9B8CFF]/40 hover:bg-[#161622] transition-all flex flex-col justify-between cursor-pointer group shadow-sm text-left"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-[10px] font-mono text-[#9B8CFF] uppercase">
                  {article.category}
                </span>
                <span className="text-[10px] text-[#626270] font-mono">{article.readTime}</span>
              </div>

              <h3 className="text-sm font-semibold text-[#F4F4F7] group-hover:text-[#B6A9FF] transition-colors leading-snug mb-2">
                {article.title}
              </h3>

              <p className="text-xs text-[#92929F] line-clamp-3 leading-relaxed mb-4">
                {article.excerpt}
              </p>
            </div>

            <div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {article.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/[0.05] text-[#92929F]"
                  >
                    #{tag}
                  </span>
                ))}
              </div>

              <div className="pt-3 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-[#626270]">
                <span>Updated: {article.lastUpdated}</span>
                <span className="text-[#9B8CFF] flex items-center gap-1 font-mono text-[10px]">
                  <CheckCircle2 className="w-3 h-3" /> Indexed in Demo
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Article Detail Preview Modal with MarkdownRenderer */}
      {selectedArticle && (
        <Modal
          isOpen={!!selectedArticle}
          onClose={() => setSelectedArticle(null)}
          title={selectedArticle.title}
          subtitle={`Category: ${selectedArticle.category} • Demo dataset`}
          maxWidth="2xl"
        >
          <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
            <div className="p-3 rounded-lg bg-[#0D0D13] border border-white/[0.06] flex items-center justify-between text-xs">
              <span className="text-[#92929F] flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#9B8CFF]" />
                Indexed in persistent memory store (Simulation)
              </span>
              <span className="font-mono text-[#B6A9FF] text-[10px]">Ready</span>
            </div>

            <div className="bg-[#161622] p-4 rounded-xl border border-white/[0.06]">
              <MarkdownRenderer content={selectedArticle.content} />
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              {selectedArticle.tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-full text-xs font-mono bg-white/[0.06] text-[#92929F]"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        </Modal>
      )}

      {/* Create Article Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Add Knowledge Article (Demo)"
        subtitle="Articles are simulated as ingested into the persistent memory retrieval store"
        maxWidth="lg"
      >
        <form onSubmit={handleCreateArticle} className="space-y-4 text-xs">
          <div>
            <label className="block text-[#92929F] font-medium mb-1">Article Title</label>
            <input
              type="text"
              required
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g., Firmware 3.2.0 Audio Codec Reset..."
              className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5 focus:outline-none focus:border-[#9B8CFF]/50"
            />
          </div>

          <div>
            <label className="block text-[#92929F] font-medium mb-1">Category</label>
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value as KnowledgeArticle['category'])}
              className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5 focus:outline-none focus:border-[#9B8CFF]/50"
            >
              <option value="Audio & Connectivity">Audio & Connectivity</option>
              <option value="Hardware">Hardware</option>
              <option value="Troubleshooting">Troubleshooting</option>
              <option value="Policies">Policies</option>
              <option value="Account & Billing">Account & Billing</option>
            </select>
          </div>

          <div>
            <label className="block text-[#92929F] font-medium mb-1">Summary Excerpt</label>
            <input
              type="text"
              value={newExcerpt}
              onChange={(e) => setNewExcerpt(e.target.value)}
              placeholder="Brief diagnostic summary for fast vector lookup..."
              className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5 focus:outline-none focus:border-[#9B8CFF]/50"
            />
          </div>

          <div>
            <label className="block text-[#92929F] font-medium mb-1">Article Body (Markdown)</label>
            <textarea
              rows={5}
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="Provide step-by-step diagnostic procedures, CLI commands, or policy conditions..."
              className="w-full bg-[#191923] text-sm text-[#F4F4F7] border border-white/[0.08] rounded-lg p-2.5 focus:outline-none focus:border-[#9B8CFF]/50 font-mono text-xs resize-none"
            />
          </div>

          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Publish & Index Article
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
