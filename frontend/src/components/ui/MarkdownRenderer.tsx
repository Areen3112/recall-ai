import { useState } from 'react';
import type React from 'react';
import { Copy, Check, AlertTriangle } from 'lucide-react';

export interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
}) => {
  // Parse blocks: code blocks, headings, lists, quotes, paragraphs
  const renderContent = () => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeLanguage = '';
    let codeBuffer: string[] = [];
    let listBuffer: { type: 'ul' | 'ol'; items: string[] } | null = null;
    let keyIdx = 0;

    const flushList = () => {
      if (!listBuffer) return;
      const { type, items } = listBuffer;
      if (type === 'ul') {
        elements.push(
          <ul key={`ul-${keyIdx++}`} className="my-2 space-y-1.5 pl-4 list-disc marker:text-[#9B8CFF]">
            {items.map((item, i) => (
              <li key={i} className="text-xs sm:text-sm leading-relaxed text-[#F4F4F7]">
                {parseInlineFormatting(item)}
              </li>
            ))}
          </ul>
        );
      } else {
        elements.push(
          <ol key={`ol-${keyIdx++}`} className="my-2 space-y-1.5 pl-4 list-decimal marker:text-[#9B8CFF] marker:font-mono">
            {items.map((item, i) => (
              <li key={i} className="text-xs sm:text-sm leading-relaxed text-[#F4F4F7]">
                {parseInlineFormatting(item)}
              </li>
            ))}
          </ol>
        );
      }
      listBuffer = null;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Handle Code Block start/end
      if (line.trim().startsWith('```')) {
        flushList();
        if (inCodeBlock) {
          // Closing code block
          const fullCode = codeBuffer.join('\n');
          elements.push(
            <CodeBlockComponent
              key={`code-${keyIdx++}`}
              code={fullCode}
              language={codeLanguage || 'bash'}
            />
          );
          codeBuffer = [];
          inCodeBlock = false;
          codeLanguage = '';
        } else {
          // Opening code block
          inCodeBlock = true;
          codeLanguage = line.trim().slice(3).trim();
          codeBuffer = [];
        }
        continue;
      }

      if (inCodeBlock) {
        codeBuffer.push(line);
        continue;
      }

      // Empty line
      if (!line.trim()) {
        flushList();
        continue;
      }

      // Caution or Alert Callout: lines starting with "> [!CAUTION]" or "> "
      if (line.trim().startsWith('> [!CAUTION]') || line.trim().startsWith('> [!WARNING]')) {
        flushList();
        // Read ahead for full quote text
        const quoteLines: string[] = [line.replace(/^>\s*\[!(CAUTION|WARNING)\]\s*/, '')];
        while (i + 1 < lines.length && lines[i + 1].trim().startsWith('>')) {
          i++;
          quoteLines.push(lines[i].replace(/^>\s*/, ''));
        }
        elements.push(
          <div
            key={`alert-${keyIdx++}`}
            className="my-3 p-3 rounded-xl bg-[#1A1017] border border-[#F43F5E]/40 text-xs text-[#FB7185] flex items-start gap-2.5 glow-rose-sm"
          >
            <AlertTriangle className="w-4 h-4 text-[#F43F5E] shrink-0 mt-0.5" />
            <div className="space-y-1 text-left">
              <span className="font-semibold uppercase tracking-wider text-[10px] text-[#FF6B8B] block">
                Caution: Host Diagnostic Action
              </span>
              <div className="text-[#F4F4F7] leading-relaxed">
                {parseInlineFormatting(quoteLines.join(' '))}
              </div>
            </div>
          </div>
        );
        continue;
      }

      // Standard Blockquote
      if (line.trim().startsWith('>')) {
        flushList();
        elements.push(
          <blockquote
            key={`quote-${keyIdx++}`}
            className="my-2 pl-3 border-l-2 border-[#9B8CFF]/50 text-xs sm:text-sm text-[#92929F] italic"
          >
            {parseInlineFormatting(line.replace(/^>\s*/, ''))}
          </blockquote>
        );
        continue;
      }

      // Headings
      if (line.startsWith('### ')) {
        flushList();
        elements.push(
          <h4
            key={`h4-${keyIdx++}`}
            className="text-xs sm:text-sm font-bold text-[#F4F4F7] tracking-tight mt-3 mb-1.5"
          >
            {parseInlineFormatting(line.slice(4))}
          </h4>
        );
        continue;
      }
      if (line.startsWith('## ')) {
        flushList();
        elements.push(
          <h3
            key={`h3-${keyIdx++}`}
            className="text-sm sm:text-base font-bold text-[#F4F4F7] tracking-tight mt-3.5 mb-1.5"
          >
            {parseInlineFormatting(line.slice(3))}
          </h3>
        );
        continue;
      }
      if (line.startsWith('# ')) {
        flushList();
        elements.push(
          <h2
            key={`h2-${keyIdx++}`}
            className="text-base sm:text-lg font-bold text-[#F4F4F7] tracking-tight mt-4 mb-2"
          >
            {parseInlineFormatting(line.slice(2))}
          </h2>
        );
        continue;
      }

      // Numbered List (e.g. "1. Step...")
      const numMatch = line.match(/^(\d+)\.\s+(.*)$/);
      if (numMatch) {
        if (!listBuffer || listBuffer.type !== 'ol') {
          flushList();
          listBuffer = { type: 'ol', items: [] };
        }
        listBuffer.items.push(numMatch[2]);
        continue;
      }

      // Unordered List (e.g. "- Item" or "* Item")
      const bulletMatch = line.match(/^[-*]\s+(.*)$/);
      if (bulletMatch) {
        if (!listBuffer || listBuffer.type !== 'ul') {
          flushList();
          listBuffer = { type: 'ul', items: [] };
        }
        listBuffer.items.push(bulletMatch[1]);
        continue;
      }

      // Standard paragraph
      flushList();
      elements.push(
        <p
          key={`p-${keyIdx++}`}
          className="text-xs sm:text-sm leading-relaxed text-[#F4F4F7] my-1.5"
        >
          {parseInlineFormatting(line)}
        </p>
      );
    }

    flushList();
    return elements;
  };

  return <div className={`space-y-1 ${className}`}>{renderContent()}</div>;
};

// Component for Fenced Code Block with Copy function
interface CodeBlockProps {
  code: string;
  language: string;
}

const CodeBlockComponent: React.FC<CodeBlockProps> = ({ code, language }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2.5 rounded-xl overflow-hidden border border-white/[0.08] bg-[#0A0A0F] shadow-sm">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-[#12121A] border-b border-white/[0.06] text-[11px] font-mono text-[#626270]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-white/[0.2]" />
          <span className="text-[#92929F] uppercase">{language || 'code'}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[#92929F] hover:text-[#F4F4F7] hover:bg-white/[0.06] px-2 py-0.5 rounded transition-colors cursor-pointer"
          title="Copy command to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-[#10B981]" />
              <span className="text-[#10B981]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Body */}
      <pre className="p-3.5 overflow-x-auto text-xs font-mono text-[#B6A9FF] leading-relaxed selection:bg-[#9B8CFF]/30">
        <code>{code}</code>
      </pre>
    </div>
  );
};

// Helper for inline markdown: **bold**, *italic*, `code`
function parseInlineFormatting(text: string): React.ReactNode[] {
  // Regex splitting by bold (**...**), inline code (`...`), and italics (*...*)
  const tokens = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);

  return tokens.map((token, index) => {
    if (token.startsWith('**') && token.endsWith('**') && token.length >= 4) {
      return (
        <strong key={index} className="font-semibold text-[#F4F4F7]">
          {token.slice(2, -2)}
        </strong>
      );
    }
    if (token.startsWith('`') && token.endsWith('`') && token.length >= 2) {
      return (
        <code
          key={index}
          className="px-1.5 py-0.5 rounded bg-white/[0.08] text-[#B6A9FF] font-mono text-[11px] border border-white/[0.06]"
        >
          {token.slice(1, -1)}
        </code>
      );
    }
    if (token.startsWith('*') && token.endsWith('*') && token.length >= 2) {
      return (
        <em key={index} className="italic text-[#92929F]">
          {token.slice(1, -1)}
        </em>
      );
    }
    return token;
  });
}
