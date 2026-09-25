"use client";

import { useRef, useState } from "react";

import {
  DOCUMENT_CATEGORY_LABEL,
  DOCUMENT_STATUS_LABEL,
  fetchDocuments,
  submitDocumentUrl,
  uploadDocument,
  type DocumentCategory,
  type DocumentStatus,
  type IntakeDocument,
} from "@/lib/api";

/**
 * File upload + website submission, and the resulting document list.
 *
 * Every submission ends up with a status and, once processed, a category and
 * a confidence — never a silent accept. A document the classifier can't
 * confidently place renders as "Not recognised" rather than being forced into
 * the nearest category: the same posture INSUFFICIENT_EVIDENCE takes toward a
 * test verdict, applied here to what was actually submitted. [PRD P1]
 */
export function IntakePortal({
  engagementId,
  initialDocuments,
}: {
  engagementId: number;
  initialDocuments: IntakeDocument[];
}) {
  const [documents, setDocuments] = useState<IntakeDocument[]>(initialDocuments);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function refresh() {
    const latest = await fetchDocuments(engagementId);
    if (latest) setDocuments(latest);
  }

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setBusy(true);
    setError(null);

    for (const file of Array.from(files)) {
      const outcome = await uploadDocument(engagementId, file);
      if (outcome.kind === "rejected") {
        setError(`${file.name}: ${outcome.detail}`);
      } else if (outcome.kind === "unreachable") {
        setError("The API is unreachable. The document was not submitted.");
      }
    }

    await refresh();
    setBusy(false);
  }

  async function handleUrlSubmit() {
    if (!url.trim()) return;
    setBusy(true);
    setError(null);

    const outcome = await submitDocumentUrl(engagementId, url.trim());
    if (outcome.kind === "rejected") {
      setError(outcome.detail);
    } else if (outcome.kind === "unreachable") {
      setError("The API is unreachable. The URL was not submitted.");
    } else {
      setUrl("");
    }

    await refresh();
    setBusy(false);
  }

  return (
    <div className="flex flex-col gap-6">
      <section className="sheet p-5 md:p-6" aria-labelledby="intake-heading">
        <h3 id="intake-heading">Submit a document or website</h3>

        <div className="mt-5 flex flex-col gap-5 lg:flex-row">
          {/* Dropzone */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => fileInput.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && fileInput.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              void handleFiles(e.dataTransfer.files);
            }}
            data-selected={dragOver ? "true" : "false"}
            className="toggle min-h-[7rem] flex-1 cursor-pointer flex-col items-center justify-center gap-1 border-dashed text-center"
          >
            <span className="font-semibold">
              {busy ? "Processing…" : "Drop a file, or click to choose"}
            </span>
            <span className="text-meta text-ink-3">
              PDF, Word, Excel, HTML or plain text
            </span>
            <input
              ref={fileInput}
              type="file"
              multiple
              accept=".pdf,.docx,.xlsx,.csv,.html,.htm,.txt"
              onChange={(e) => void handleFiles(e.target.files)}
              className="sr-only"
            />
          </div>

          {/* URL submission */}
          <div className="flex flex-1 flex-col gap-2">
            <label htmlFor="intake-url" className="label">
              Or a website URL
            </label>
            <div className="flex gap-2">
              <input
                id="intake-url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void handleUrlSubmit()}
                placeholder="https://example.org/privacy-notice"
                className="field flex-1"
              />
              <button
                type="button"
                onClick={() => void handleUrlSubmit()}
                disabled={busy || !url.trim()}
                className="btn btn-primary"
              >
                Submit
              </button>
            </div>
            <p className="m-0 text-meta text-ink-3">
              Fetched once, over HTTPS/HTTP only. A URL resolving to a private
              or internal address is refused before any request is made.
            </p>
          </div>
        </div>

        {busy && <div className="indeterminate-rule mt-4" />}

        {error && (
          <p role="alert" className="m-0 mt-4 border-l-4 border-fail bg-inset px-4 py-3 text-sm text-ink">
            {error}
          </p>
        )}
      </section>

      <DocumentList documents={documents} />
    </div>
  );
}

const STATUS_CHIP_CLASS: Record<DocumentStatus, string> = {
  RECEIVED: "border border-control text-ink-2",
  PROCESSING: "border border-control text-ink-2",
  EXTRACTED: "border border-control text-ink-2",
  CLASSIFIED: "bg-pass text-on-verdict",
  REJECTED: "bg-fail text-on-verdict",
  FAILED: "bg-fail text-on-verdict",
};

function DocumentList({ documents }: { documents: IntakeDocument[] }) {
  if (documents.length === 0) {
    return (
      <section className="sheet p-5 text-sm text-ink-2">
        No documents submitted for this engagement yet.
      </section>
    );
  }

  return (
    <section className="sheet" aria-labelledby="documents-heading">
      <header className="bg-band px-5 py-4 text-on-band">
        <h3 id="documents-heading" className="text-on-band">
          Submitted documents
        </h3>
        <p className="m-0 mt-1 font-mono text-meta text-on-band-2">
          {documents.length} document{documents.length === 1 ? "" : "s"}
        </p>
      </header>

      <div className="scroll-x">
        <table className="data-table min-w-[52rem]">
          <thead>
            <tr>
              <th scope="col">Name / source</th>
              <th scope="col" className="w-32">Status</th>
              <th scope="col" className="w-48">Classification</th>
              <th scope="col" className="w-28">Size</th>
              <th scope="col" className="w-40">Submitted</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <DocumentRow key={doc.id} doc={doc} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DocumentRow({ doc }: { doc: IntakeDocument }) {
  const category = doc.classification?.category as DocumentCategory | undefined;
  const label = category ? DOCUMENT_CATEGORY_LABEL[category] ?? category : null;

  return (
    <tr className="row-interactive">
      <td>
        <div className="font-medium text-ink">{doc.original_name}</div>
        <div className="text-meta text-ink-3">
          {doc.source_type === "URL" ? "Website" : "Upload"}
          {doc.detected_mime ? ` / ${doc.detected_mime}` : ""}
        </div>
        {doc.rejection_reason && (
          <div className="mt-1 text-meta text-fail">{doc.rejection_reason}</div>
        )}
      </td>
      <td>
        <span className={`chip ${STATUS_CHIP_CLASS[doc.status]}`}>
          {DOCUMENT_STATUS_LABEL[doc.status]}
        </span>
      </td>
      <td>
        {label ? (
          <div>
            <span className="font-medium text-ink">{label}</span>
            <div className="text-meta text-ink-3">
              {Math.round((doc.classification?.confidence ?? 0) * 100)}% confidence
            </div>
          </div>
        ) : (
          <span className="text-meta text-ink-3">not yet classified</span>
        )}
      </td>
      <td className="font-mono text-ink">{formatBytes(doc.size_bytes)}</td>
      <td className="font-mono text-meta text-ink-2">
        {new Date(doc.created_at).toLocaleString()}
      </td>
    </tr>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
