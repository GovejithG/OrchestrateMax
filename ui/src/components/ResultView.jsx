import { useState } from "react";
import { Copy, Check, AlertTriangle, CheckCircle } from "lucide-react";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import python from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import javascript from "react-syntax-highlighter/dist/esm/languages/hljs/javascript";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import useStore from "../store/useStore";

SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("javascript", javascript);

function extractCodeBlocks(text) {
    const blocks = [];
    const regex = /```(\w+)?\n([\s\S]*?)```/g;
    let match;
    while ((match = regex.exec(text)) !== null) {
        blocks.push({ lang: match[1] || "python", code: match[2].trim() });
    }
    return blocks;
}

function CopyButton({ text }) {
    const [copied, setCopied] = useState(false);
    const handleCopy = () => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };
    return (
        <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors"
        >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? "Copied" : "Copy"}
        </button>
    );
}

function ReviewerScore({ content }) {
    if (!content) return null;
    const scoreMatch = content.match(/SCORE:\s*(\d+)\/10/i);
    const verdictMatch = content.match(/VERDICT:\s*(PASS|FAIL)/i);
    if (!scoreMatch && !verdictMatch) return null;

    const score = scoreMatch ? parseInt(scoreMatch[1]) : null;
    const verdict = verdictMatch ? verdictMatch[1] : null;
    const isPass = verdict === "PASS";

    return (
        <div className={`flex items-center gap-3 p-3 rounded-lg border mb-4 ${
            isPass
                ? "border-emerald-500/30 bg-emerald-500/10"
                : "border-red-500/30 bg-red-500/10"
        }`}>
            {isPass
                ? <CheckCircle size={18} className="text-emerald-400 flex-shrink-0" />
                : <AlertTriangle size={18} className="text-red-400 flex-shrink-0" />
            }
            <div>
                <p className={`text-sm font-semibold ${isPass ? "text-emerald-400" : "text-red-400"}`}>
                    {verdict} — {score}/10
                </p>
                <p className="text-xs text-zinc-500">Reviewer assessment</p>
            </div>
        </div>
    );
}

function SectionBlock({ section, content }) {
    const codeBlocks = extractCodeBlocks(content);

    const SECTION_LABELS = {
        PLAN: "Plan",
        CODE: "Code",
        REVIEW: "Review",
    };

    return (
        <div className="mb-6">
            {/* Section header */}
            <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-bold uppercase tracking-widest text-zinc-500">
                    {SECTION_LABELS[section] || section}
                </span>
                <div className="flex-1 h-px bg-zinc-800" />
            </div>

            {/* Review score badge sits above review text */}
            {section === "REVIEW" && <ReviewerScore content={content} />}

            {/* Code blocks with syntax highlighting */}
            {codeBlocks.length > 0 ? (
                <div className="space-y-4">
                    {codeBlocks.map((block, j) => (
                        <div key={j} className="rounded-lg overflow-hidden border border-zinc-700">
                            <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-800 border-b border-zinc-700">
                                <span className="text-xs text-zinc-400 font-mono">{block.lang}</span>
                                <CopyButton text={block.code} />
                            </div>
                            <SyntaxHighlighter
                                language={block.lang}
                                style={atomOneDark}
                                customStyle={{
                                    margin: 0,
                                    padding: "1rem",
                                    fontSize: "12px",
                                    background: "#18181b",
                                }}
                            >
                                {block.code}
                            </SyntaxHighlighter>
                        </div>
                    ))}
                </div>
            ) : (
                /* Plain text — plan and review */
                <div className="bg-zinc-900 rounded-lg border border-zinc-700 p-4">
                    <pre className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed font-mono">
                        {content}
                    </pre>
                </div>
            )}
        </div>
    );
}

export default function ResultView() {
    const { sections, runStatus } = useStore();

    if (sections.length === 0) {
        return (
            <div className="flex items-center justify-center h-32">
                <p className="text-zinc-600 text-sm">
                    {runStatus === "running"
                        ? "Waiting for first agent to complete..."
                        : "Output will appear here"}
                </p>
            </div>
        );
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
                    Result
                </span>
            </div>
            {sections.map((s, i) => (
                <SectionBlock key={i} section={s.section} content={s.content} />
            ))}
        </div>
    );
}
