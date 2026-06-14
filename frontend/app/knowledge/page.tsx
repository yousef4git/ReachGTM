"use client";

import { useState, useCallback, useRef, type FormEvent } from "react";
import { knowledgeApi } from "@/lib/api";
import { useStore } from "@/store/useStore";
import { useQuery } from "@tanstack/react-query";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Trash2, X, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { KnowledgeDocument } from "@/types";

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
  const addKnowledgeDoc = useStore((s) => s.addKnowledgeDoc);
  const { data: docs, isLoading, error } = useKnowledgeList();
  const knowledgeDocs = useStore((s) => s.knowledgeDocs);

  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState(DOC_TYPE_OPTIONS[0].value);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const allDocs = docs ?? knowledgeDocs;

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && (dropped.name.endsWith(".pdf") || dropped.name.endsWith(".docx") || dropped.name.endsWith(".doc"))) {
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
        const result = await knowledgeApi.upload(file, docType);
        addKnowledgeDoc(result);
        setUploadSuccess(`${file.name} uploaded and indexed successfully.`);
        setFile(null);
        if (inputRef.current) inputRef.current.value = "";
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [file, docType, addKnowledgeDoc]
  );

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload product documentation, sales decks, and other materials to power your GTM agents.
          </p>
        </div>

        {/* Upload Form */}
        <form onSubmit={handleUpload} className="mb-8 space-y-4">
          {/* Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={cn(
              "cursor-pointer rounded-xl border-2 border-dashed bg-white p-10 text-center transition-colors",
              dragOver
                ? "border-blue-400 bg-blue-50"
                : file
                  ? "border-green-300 bg-green-50"
                  : "border-gray-300 hover:border-gray-400"
            )}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.doc"
              onChange={handleFileSelect}
              className="hidden"
            />

            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="h-8 w-8 text-green-500" />
                <div className="text-left">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(0)} KB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setFile(null); if (inputRef.current) inputRef.current.value = ""; }}
                  className="rounded-full p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div>
                <Upload className="mx-auto mb-3 h-8 w-8 text-gray-400" />
                <p className="text-sm font-medium text-gray-700">
                  Drop a PDF or DOCX here, or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-400">
                  Supports .pdf, .docx, .doc
                </p>
              </div>
            )}
          </div>

          {/* Document Type */}
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold text-gray-900">Document Type</h2>
            <div className="flex flex-wrap gap-2">
              {DOC_TYPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setDocType(opt.value)}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 text-sm transition-colors",
                    docType === opt.value
                      ? "border-blue-300 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={!file || uploading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {uploading ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Uploading & Indexing…</>
            ) : (
              <><Upload className="h-4 w-4" /> Upload Document</>
            )}
          </button>

          {uploadError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {uploadError}
            </div>
          )}

          {uploadSuccess && (
            <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
              <CheckCircle className="h-4 w-4 shrink-0" />
              {uploadSuccess}
            </div>
          )}
        </form>

        {/* Document List */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Uploaded Documents
            {allDocs.length > 0 && (
              <span className="ml-2 text-sm font-normal text-gray-400">({allDocs.length})</span>
            )}
          </h2>

          {isLoading && (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            </div>
          )}

          {!isLoading && allDocs.length === 0 && (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
              <BookOpen className="mx-auto mb-3 h-8 w-8 text-gray-300" />
              <p className="text-sm font-medium text-gray-700">No documents uploaded yet</p>
              <p className="mt-1 text-xs text-gray-400">
                Upload a PDF or DOCX above to power your GTM agents with company knowledge.
              </p>
            </div>
          )}

          {allDocs.length > 0 && (
            <div className="space-y-3">
              {allDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-xl border bg-white px-5 py-4 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                      <p className="text-xs text-gray-400">
                        {DOC_TYPE_OPTIONS.find((o) => o.value === doc.doc_type)?.label ?? doc.doc_type}
                        {doc.chunk_count !== null && doc.chunk_count !== undefined && (
                          <> · {doc.chunk_count} chunks</>
                        )}
                        <> · {new Date(doc.created_at).toLocaleDateString()}</>
                      </p>
                    </div>
                  </div>
                  <span className={cn(
                    "rounded-full px-2.5 py-0.5 text-xs font-medium",
                    doc.status === "indexed" ? "bg-green-100 text-green-700" :
                    doc.status === "failed" ? "bg-red-100 text-red-700" :
                    "bg-yellow-100 text-yellow-700"
                  )}>
                    {doc.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
