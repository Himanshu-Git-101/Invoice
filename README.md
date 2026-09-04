# 🎙️ InVoice — Voice In. Invoices Out. Zero Data Entry ERP.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Framework: Streamlit](https://img.shields.io/badge/framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![AI Engine: Gemini 2.5](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4.svg)](https://deepmind.google/technologies/gemini/)
[![ERP Sync: Tally Prime](https://img.shields.io/badge/ERP-Tally%20Prime%20Sync-008080.svg)](https://tallysolutions.com/)
[![Compliance: CBIC Rule 46](https://img.shields.io/badge/Compliance-CBIC%20Rule%2046%20GST-059669.svg)](https://www.cbic.gov.in/)

> **InVoice** is an enterprise-grade, voice-driven AI Gateway designed to eliminate manual invoice entry for ERP systems like **Tally Prime, SAP S/4HANA, Oracle NetSuite, and Odoo**. By leveraging **Google Gemini 2.5 Flash**, InVoice transforms continuous, multi-item natural spoken speech into 100% compliant Indian GST vouchers and structured Tally Prime XML payloads instantly.

---

## 🌟 Key Features

### 🇮🇳 100% Indian GST & CBIC Rule 46 Compliance
- **Complete GST Tax Slab Coverage**: Supports 0%, 3%, 5%, 12%, 18%, 28%, and Sin Tax CESS slabs (40%, 60%, 70%).
- **Sin Tax & GST Compensation CESS Engine**: Automatically applies 70% total effective tax (28% Base GST + 42% CESS) for Tobacco/Cigarettes (HSN `2402`), 60% for Pan Masala (HSN `2106`), and 40% for Aerated Drinks (HSN `2202`).
- **Dual Tax Structure**: Handles Intra-State Supply (CGST + SGST) vs Inter-State Supply (IGST).
- **Vendor GSTIN & Place of Supply (POS)**: Manages 15-digit Indian GSTINs, Place of Supply state codes, and Reverse Charge (RCM) flags.
- **Master HSN/SAC Engine**: Automatic lookup across 150+ raw materials, metals (TMT, Steel, Copper), chemicals, textiles, pharmaceuticals, IT equipment, and SAC service codes.

### 🧠 Multi-Item Conversational AI Extraction
- **Instant Speech-to-ERP Processing**: Extract multi-item invoices (e.g., *"Purchased 100 packs of Cigarettes at 350 rate with 5% discount and 20 Laptops at 45000 rate from ITC Distributors bill 808"*) in real-time.
- **Dynamic Slot Filling**: Powered by **Gemini 2.5 Flash**, OpenAI GPT-4o, and a domain-specific offline NLP fallback parser.
- **Zero Hardcoding**: Dynamically calculates quantities, UOM units (`Packs`, `Nos`, `Bags`, `Kg`), unit rates, trade discounts, taxable base values, tax breakups, and line totals.

### 📊 Executive Financial Dashboard & Tally ERP Sync
- **6 Metric Executive Header**: Real-time totals for Gross Subtotal, Trade Discounts, Taxable Base, CGST+SGST Tax, Compensation CESS, and Net Payable Amount.
- **Tally Prime HTTP XML Generator**: Produces complete `<ENVELOPE>` XML payloads featuring `<ALLINVENTORYENTRIES.LIST>` and `<ALLLEDGERENTRIES.LIST>` with one-click direct server injection.
- **One-Touch Reset**: Clean single **`🔄 Reset Inputs`** button to clear terminal state instantly.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[🎙️ User Speech / Text Input] --> B[⚡ InVoice Gateway / Streamlit UI]
    B --> C[🧠 Neural AI Engine - Gemini 2.5 Flash / Whisper]
    C --> D[🇮🇳 Indian GST & HSN/SAC Classification Engine]
    D --> E[📊 Financial Math & Multi-Item Slot Renderer]
    E --> F[🏛️ Tally Prime HTTP XML Payload Generator]
    F --> G[🚀 Tally Prime ERP Server / Accounting Database]
