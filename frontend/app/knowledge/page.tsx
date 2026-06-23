"use client";

import { useState, useCallback, useRef, type FormEvent } from "react";
import { knowledgeApi } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { KnowledgeDocument } from "@/types";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".pptx", ".txt", ".md", ".markdown", ".csv"];
const ACCEPTED_ATTR = ACCEPTED_EXTENSIONS.join(",");

const DOC_TYPE_OPTIONS = [
  { value: "product_doc", label: "Product Documentation" },
  { value: "sales_deck", label: "Sales Deck / Pitch" },
  { value: "case_study", label: "Case Study" },
  { value: "competitive_intel", label: "Competitive Intel" },
  { value: "website_content", label: "Website Content" },
  { value: "other", label: "Other" },
];

function useKnowledgeList() {
  return useQuery<KnowledgeDocument[]>({
    queryKey: ["knowledge"],
    queryFn: () => knowledgeApi.list(),
  });
}

export default function KnowledgePage() {
  const queryClient = useQueryClient();
  const { data: docs, isLoading } = useKnowledgeList();

  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState(DOC_TYPE_OPTIONS[0].value);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  // The server knowledge list is the single source of truth. We deliberately do
  // NOT fall back to the persisted localStorage store: after a cold run the DB
  // is empty, and stale/malformed local entries would otherwise render as
  // phantom documents (blank filename, "Invalid Date"). Dedupe by id as a
  // defensive guard against duplicate React keys.
  const allDocs = Array.from(
    new Map((docs ?? []).map((doc) => [doc.id, doc])).values()
  );

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && ACCEPTED_EXTENSIONS.some((ext) => dropped.name.toLowerCase().endsWith(ext))) {
      setFile(dropped);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  };

  const handleUpload = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      if (!file) return;

      setUploading(true);
      setUploadError(null);
      setUploadSuccess(null);

      try {
        await knowledgeApi.upload(file, docType);
        // The server list is authoritative; refetch so the indexed doc shows
        // its full shape (id, created_at, …) rather than the upload response.
        await queryClient.invalidateQueries({ queryKey: ["knowledge"] });
        setUploadSuccess(`${file.name} uploaded and indexed.`);
        setFile(null);
        if (inputRef.current) inputRef.current.value = "";
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [file, docType, queryClient]
  );

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      <header className="animate-rise mb-9">
        <p className="eyebrow">Grounding</p>
        <h1 className="display mt-2.5 text-[2.5rem] font-medium leading-tight text-ink">
          Knowledge base
        </h1>
        <p className="mt-2 max-w-xl text-[0.9375rem] text-ink-muted">
          Upload product docs, decks, and case studies. The agents read them to
          stay grounded in your voice and facts.
        </p>
      </header>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="mb-10 space-y-4">
        {/* Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={cn(
            "cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-colors",
            dragOver
              ? "border-flare-500 bg-flare-50"
              : file
                ? "border-success bg-success-tint"
                : "border-hairline-strong bg-surface hover:border-ink-faint"
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_ATTR}
            onChange={handleFileSelect}
            className="hidden"
          />

          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="h-8 w-8 text-success" />
              <div className="text-left">
                <p className="font-semibold text-ink">{file.name}</p>
                <p className="mono text-[0.6875rem] text-ink-faint">
                  {(file.size / 1024).toFixed(0)} KB
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  if (inputRef.current) inputRef.current.value = "";
                }}
                className="rounded-full p-1 text-ink-faint hover:bg-sunken hover:text-ink"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div>
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-sunken text-ink-muted">
                <Upload className="h-5 w-5" />
              </span>
              <p className="mt-3 text-[0.9375rem] font-semibold text-ink">
                Drop a document, or click to browse
              </p>
              <p className="mono mt-1 text-[0.6875rem] text-ink-faint">
                .pdf · .docx · .pptx · .md · .txt · .csv
              </p>
            </div>
          )}
        </div>

        {/* Document Type */}
        <div className="card p-5">
          <h2 className="eyebrow mb-3">Document type</h2>
          <div className="flex flex-wrap gap-2">
            {DOC_TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setDocType(opt.value)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-[0.8125rem] font-medium transition-colors",
                  docType === opt.value
                    ? "border-flare-600 bg-flare-50 text-flare-700"
                    : "border-hairline-strong text-ink-muted hover:border-ink-faint hover:text-ink"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={!file || uploading}
          className="btn btn-flare w-full py-3.5 text-[0.9375rem]"
        >
          {uploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Uploading & indexing…
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" /> Upload document
            </>
          )}
        </button>

        {uploadError && (
          <div className="alert alert-danger">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {uploadError}
          </div>
        )}
        {uploadSuccess && (
          <div className="alert alert-success">
            <CheckCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {uploadSuccess}
          </div>
        )}
      </form>

      {/* Document List */}
      <div className="flex items-center gap-3">
        <h2 className="eyebrow !text-ink-muted">
          Indexed documents{allDocs.length > 0 && ` · ${allDocs.length}`}
        </h2>
        <div className="rule flex-1" />
      </div>

      <div className="mt-5">
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-flare-600" />
          </div>
        )}

        {!isLoading && allDocs.length === 0 && (
          <div className="rounded-2xl border border-dashed border-hairline-strong bg-surface p-14 text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-sunken text-ink-faint">
              <BookOpen className="h-6 w-6" />
            </span>
            <p className="mt-4 text-[1.0625rem] font-semibold text-ink">
              No documents yet
            </p>
            <p className="mx-auto mt-1.5 max-w-sm text-[0.875rem] text-ink-muted">
              Upload a deck, doc, or PDF to ground your agents in company knowledge.
            </p>
          </div>
        )}

        {allDocs.length > 0 && (
          <div className="stagger space-y-2.5">
            {allDocs.map((doc) => (
              <div
                key={doc.id}
                className="card flex items-center justify-between px-5 py-4"
              >
                <div className="flex min-w-0 items-center gap-3.5">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-sunken text-ink-muted">
                    <FileText className="h-5 w-5" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-[0.875rem] font-semibold text-ink">
                      {doc.filename}
                    </p>
                    <p className="mono mt-0.5 text-[0.6875rem] text-ink-faint">
                      {DOC_TYPE_OPTIONS.find((o) => o.value === doc.doc_type)
                        ?.label ?? doc.doc_type}
                      {doc.chunk_count !== null &&
                        doc.chunk_count !== undefined && (
                          <> · {doc.chunk_count} chunks</>
                        )}
                      {" · "}
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span
                  className={cn(
                    "chip shrink-0",
                    doc.status === "indexed"
                      ? "chip-success"
                      : doc.status === "failed"
                        ? "chip-danger"
                        : "chip-warn"
                  )}
                >
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
