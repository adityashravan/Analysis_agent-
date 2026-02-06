#!/usr/bin/env python
"""
Document Management CLI
Add, list, search, and remove internal documents for agent context.

This tool allows you to manage internal company documents (PDFs, policies, configs)
that agents use alongside online scraped data for comprehensive analysis.

Usage Examples:
    # Add a Kubernetes policy PDF
    python manage_docs.py add docs/k8s-policy.pdf --category kubernetes --tags policy,versions
    
    # Add an OS configuration document
    python manage_docs.py add docs/sles-config.pdf --category os --description "SLES hardening guide"
    
    # List all documents
    python manage_docs.py list
    
    # List only Kubernetes documents
    python manage_docs.py list --category kubernetes
    
    # Search for relevant documents
    python manage_docs.py search "container runtime version"
    
    # Search in specific category
    python manage_docs.py search "kubelet config" --category kubernetes
    
    # Remove a document
    python manage_docs.py remove doc_20260206_120000_policy
    
    # Show document store statistics
    python manage_docs.py stats
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.document_store import get_document_store


def cmd_add(args):
    """Add a document to the store"""
    store = get_document_store()
    
    tags = args.tags.split(",") if args.tags else []
    tags = [t.strip() for t in tags if t.strip()]
    
    try:
        result = store.ingest_document(
            file_path=args.file,
            category=args.category,
            tags=tags,
            description=args.description
        )
        
        if result["status"] == "duplicate":
            print(f"\n⚠️  Document already exists: {result['doc_id']}")
        else:
            print(f"\n✅ Document added successfully!")
            print(f"   ID: {result['doc_id']}")
            print(f"   Category: {result['category']}")
            print(f"   Chunks: {result['chunks']}")
            print(f"   Characters: {result.get('chars', 'N/A'):,}")
            
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("   Run: uv pip install pymupdf")
        sys.exit(1)


def cmd_list(args):
    """List all documents"""
    store = get_document_store()
    docs = store.list_documents(category=args.category)
    
    if not docs:
        print("\n📭 No documents found")
        if args.category:
            print(f"   (Filtered by category: {args.category})")
        print("\nTo add documents, run:")
        print("   python manage_docs.py add <file> --category <category>")
        return
    
    print(f"\n📚 Documents ({len(docs)} total)")
    if args.category:
        print(f"   (Filtered: {args.category})")
    print()
    
    # Table header
    print(f"{'ID':<45} {'Category':<12} {'Filename':<25} {'Chunks':<8} {'Tags'}")
    print("-" * 110)
    
    for doc in docs:
        tags = ", ".join(doc.get('tags', [])[:3])
        if len(doc.get('tags', [])) > 3:
            tags += "..."
        
        filename = doc['filename']
        if len(filename) > 23:
            filename = filename[:20] + "..."
            
        print(f"{doc['id']:<45} {doc['category']:<12} {filename:<25} {doc['chunk_count']:<8} {tags}")


def cmd_search(args):
    """Search documents"""
    store = get_document_store()
    
    results = store.search(
        query=args.query,
        category=args.category,
        n_results=args.limit
    )
    
    if not results:
        print(f"\n🔍 No results found for: '{args.query}'")
        if args.category:
            print(f"   (Searched in category: {args.category})")
        return
    
    print(f"\n🔍 Search Results for: '{args.query}'")
    if args.category:
        print(f"   (Category: {args.category})")
    print()
    
    for i, result in enumerate(results, 1):
        score = result['relevance_score']
        score_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        
        print(f"━━━ Result {i} ━━━ [{score_bar}] {score:.2f}")
        print(f"📄 Source: {result['source']}")
        print(f"📁 Category: {result['category']}")
        
        # Show text preview
        text = result['text']
        if len(text) > 300:
            text = text[:300] + "..."
        print(f"\n{text}\n")


def cmd_remove(args):
    """Remove a document"""
    store = get_document_store()
    
    # Confirm removal
    if not args.force:
        confirm = input(f"Remove document '{args.doc_id}'? [y/N]: ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    if store.remove_document(args.doc_id):
        print(f"\n✅ Document removed: {args.doc_id}")
    else:
        print(f"\n❌ Document not found: {args.doc_id}")
        print("\nTo see available documents, run:")
        print("   python manage_docs.py list")


def cmd_stats(args):
    """Show document store statistics"""
    store = get_document_store()
    stats = store.get_stats()
    
    print("\n📊 Document Store Statistics")
    print("=" * 40)
    print(f"Total Documents:  {stats['total_documents']}")
    print(f"Total Chunks:     {stats['total_chunks']}")
    print(f"Total Characters: {stats['total_chars']:,}")
    print()
    
    if stats['by_category']:
        print("By Category:")
        print("-" * 40)
        for cat, data in stats['by_category'].items():
            print(f"  {cat:<15} {data['count']:>3} docs, {data['chunks']:>5} chunks")
    
    print()
    print(f"Store Location: {store.store_path}")


def cmd_context(args):
    """Get context for an agent (debug tool)"""
    store = get_document_store()
    
    context = store.get_context_for_agent(
        agent_type=args.agent,
        query=args.query,
        max_chars=args.max_chars
    )
    
    print(f"\n🤖 Context for Agent: {args.agent}")
    print(f"🔍 Query: {args.query}")
    print(f"📊 Results: {context['chunks_used']} chunks, {context['total_chars']:,} chars")
    print()
    
    if context['sources']:
        print("Sources:")
        for src in context['sources']:
            print(f"  📄 {src}")
        print()
    
    if args.show_context:
        print("=" * 60)
        print("CONTEXT:")
        print("=" * 60)
        print(context['context'])


def main():
    parser = argparse.ArgumentParser(
        description="Manage internal documents for OS/K8s Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_docs.py add docs/policy.pdf -c kubernetes -t policy,versions
  python manage_docs.py list
  python manage_docs.py search "container runtime"
  python manage_docs.py remove doc_20260206_120000_policy
  python manage_docs.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # === ADD command ===
    add_parser = subparsers.add_parser("add", help="Add a document to the store")
    add_parser.add_argument("file", help="Path to document (PDF, TXT, MD)")
    add_parser.add_argument("--category", "-c", 
                           choices=["kubernetes", "os", "general"],
                           default="general",
                           help="Document category (default: general)")
    add_parser.add_argument("--tags", "-t", 
                           help="Comma-separated tags (e.g., 'policy,versions')")
    add_parser.add_argument("--description", "-d",
                           help="Human-readable description")
    
    # === LIST command ===
    list_parser = subparsers.add_parser("list", help="List all documents")
    list_parser.add_argument("--category", "-c",
                            choices=["kubernetes", "os", "general"],
                            help="Filter by category")
    
    # === SEARCH command ===
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--category", "-c",
                              choices=["kubernetes", "os", "general"],
                              help="Filter by category")
    search_parser.add_argument("--limit", "-n", type=int, default=5,
                              help="Number of results (default: 5)")
    
    # === REMOVE command ===
    remove_parser = subparsers.add_parser("remove", help="Remove a document")
    remove_parser.add_argument("doc_id", help="Document ID to remove")
    remove_parser.add_argument("--force", "-f", action="store_true",
                              help="Skip confirmation prompt")
    
    # === STATS command ===
    stats_parser = subparsers.add_parser("stats", help="Show document store statistics")
    
    # === CONTEXT command (debug) ===
    context_parser = subparsers.add_parser("context", help="Get context for an agent (debug)")
    context_parser.add_argument("agent", choices=["kubernetes", "os", "general"],
                               help="Agent type")
    context_parser.add_argument("query", help="Context query")
    context_parser.add_argument("--max-chars", type=int, default=8000,
                               help="Maximum characters (default: 8000)")
    context_parser.add_argument("--show-context", "-s", action="store_true",
                               help="Show full context text")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\n💡 Quick start:")
        print("   python manage_docs.py add my_document.pdf --category kubernetes")
        return
    
    # Route to command handler
    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "search": cmd_search,
        "remove": cmd_remove,
        "stats": cmd_stats,
        "context": cmd_context,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
