import datetime
from _decimal import Decimal
from io import StringIO

from .datev_csv_writer import DatevCSVWriter
from .utils import parse_any_date, AnyDateRepresentation

DEFAULT_SKR_NUMBER = '04'


class BookingsCSVFile:
    def __init__(self,
                 start_date: AnyDateRepresentation,
                 end_date: AnyDateRepresentation,
                 financial_year_start: AnyDateRepresentation,
                 author_initials: str = '',
                 skr_number: str = DEFAULT_SKR_NUMBER,
                 title: str | None = None, ):
        self.start_date = start_date

        if len(title) > 30:
            raise ValueError("The `title` field can at most contain 30 characters.")
        if start_date.year != end_date.year:
            raise ValueError("The start_date and end_date fields must be within the same year.")

        self.header = [  # see: https://developer.datev.de/datev/platform/en/dtvf/formate/header
            'EXTF', 700, 21, "Buchungsstapel", 12, datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3], '', "RE",
            "MaxMuster", "", 1001, 1, datev_date(financial_year_start), 4, datev_date(start_date),
            datev_date(end_date), title or "Buchungen", author_initials, 1, '', '', "EUR", '', '',
            '', '', skr_number, '', '', "", ""
        ]
        self.title_row = [  # see: https://developer.datev.de/datev/platform/en/dtvf/einstieg
            'Umsatz (ohne Soll/Haben-Kz)', 'Soll/Haben-Kennzeichen', 'WKZ Umsatz',
            'Kurs', 'Basis-Umsatz', 'WKZ Basis-Umsatz', 'Konto', 'Gegenkonto (ohne BU-Schlüssel)',
            'BU-Schlüssel', 'Belegdatum', 'Belegfeld 1', 'Belegfeld 2', 'Skonto', 'Buchungstext',
            'Postensperre', 'Diverse Adressnummer', 'Geschäftspartnerbank', 'Sachverhalt', 'Zinssperre',
            'Beleglink', 'Beleginfo - Art 1', 'Beleginfo - Inhalt 1', 'Beleginfo - Art 2', 'Beleginfo - Inhalt 2',
            'Beleginfo - Art 3', 'Beleginfo - Inhalt 3', 'Beleginfo - Art 4', 'Beleginfo - Inhalt 4',
            'Beleginfo - Art 5', 'Beleginfo - Inhalt 5', 'Beleginfo - Art 6', 'Beleginfo - Inhalt 6',
            'Beleginfo - Art 7', 'Beleginfo - Inhalt 7', 'Beleginfo - Art 8', 'Beleginfo - Inhalt 8',
            'KOST1 - Kostenstelle', 'KOST2 - Kostenstelle', 'Kost-Menge', 'EU-Land u. UStID', 'EU-Steuersatz',
            'Abw. Versteuerungsart', 'Sachverhalt L+L', 'Funktionsergänzung L+L', 'BU 49 Hauptfunktionstyp',
            'BU 49 Hauptfunktionsnummer', 'BU 49 Funktionsergänzung', 'Zusatzinformation - Art 1',
            'Zusatzinformation- Inhalt 1', 'Zusatzinformation - Art 2', 'Zusatzinformation- Inhalt 2',
            'Zusatzinformation - Art 3', 'Zusatzinformation- Inhalt 3', 'Zusatzinformation - Art 4',
            'Zusatzinformation- Inhalt 4', 'Zusatzinformation - Art 5', 'Zusatzinformation- Inhalt 5',
            'Zusatzinformation - Art 6', 'Zusatzinformation- Inhalt 6', 'Zusatzinformation - Art 7',
            'Zusatzinformation- Inhalt 7', 'Zusatzinformation - Art 8', 'Zusatzinformation- Inhalt 8',
            'Zusatzinformation - Art 9', 'Zusatzinformation- Inhalt 9', 'Zusatzinformation - Art 10',
            'Zusatzinformation- Inhalt 10', 'Zusatzinformation - Art 11', 'Zusatzinformation- Inhalt 11',
            'Zusatzinformation - Art 12', 'Zusatzinformation- Inhalt 12', 'Zusatzinformation - Art 13',
            'Zusatzinformation- Inhalt 13', 'Zusatzinformation - Art 14', 'Zusatzinformation- Inhalt 14',
            'Zusatzinformation - Art 15', 'Zusatzinformation- Inhalt 15', 'Zusatzinformation - Art 16',
            'Zusatzinformation- Inhalt 16', 'Zusatzinformation - Art 17', 'Zusatzinformation- Inhalt 17',
            'Zusatzinformation - Art 18', 'Zusatzinformation- Inhalt 18', 'Zusatzinformation - Art 19',
            'Zusatzinformation- Inhalt 19', 'Zusatzinformation - Art 20', 'Zusatzinformation- Inhalt 20',
            'Stück', 'Gewicht', 'Zahlweise', 'Forderungsart', 'Veranlagungsjahr', 'Zugeordnete Fälligkeit',
            'Skontotyp', 'Auftragsnummer', 'Buchungstyp', 'USt-Schlüssel (Anzahlungen)', 'EU-Land (Anzahlungen)',
            'Sachverhalt L+L (Anzahlungen)', 'EU-Steuersatz (Anzahlungen)', 'Erlöskonto (Anzahlungen)',
            'Herkunft-Kz', 'Buchungs GUID', 'KOST-Datum', 'SEPA-Mandatsreferenz', 'Skontosperre',
            'Gesellschaftername', 'Beteiligtennummer', 'Identifikationsnummer', 'Zeichnernummer', 'Postensperre bis',
            'Bezeichnung SoBil-Sachverhalt', 'Kennzeichen SoBil-Buchung', 'Festschreibung', 'Leistungsdatum',
            'Datum Zuord. Steuerperiode', 'Fälligkeit', 'Generalumkehr (GU)', 'Steuersatz', 'Land'
        ]

        self.rows = []

    def add_booking(self, /,
                    revenue: Decimal,
                    debit_credit_indicator: str,
                    account: int,
                    contra_account_without_bu_key: int,
                    document_date: AnyDateRepresentation,
                    posting_text: str,
                    currency_code_revenue: str = 'EUR',
                    exchange_rate: Decimal | None = None,
                    base_revenue: Decimal | None = None,
                    currency_code_base_revenue: Decimal | None = None,
                    bu_key: str | None = None,
                    document_field_1: str | None = None,
                    document_field_2: str | None = None,
                    discount: Decimal | None = None,
                    item_block: int = 0,
                    miscellaneous_address_number: str | None = None,
                    business_partner_bank: int | None = None,
                    issue: int | None = None,
                    interest_lock: int | None = None,
                    document_link: str | None = None,
                    document_info_type_1: str | None = None,
                    document_info_content_1: str | None = None,
                    document_info_type_2: str | None = None,
                    document_info_content_2: str | None = None,
                    document_info_type_3: str | None = None,
                    document_info_content_3: str | None = None,
                    document_info_type_4: str | None = None,
                    document_info_content_4: str | None = None,
                    document_info_type_5: str | None = None,
                    document_info_content_5: str | None = None,
                    document_info_type_6: str | None = None,
                    document_info_content_6: str | None = None,
                    document_info_type_7: str | None = None,
                    document_info_content_7: str | None = None,
                    document_info_type_8: str | None = None,
                    document_info_content_8: str | None = None,
                    cost_center_1: str | None = None,
                    cost_center_2: str | None = None,
                    cost_quantity: str | None = None,
                    eu_member_state_and_vat_id_determination: str | None = None,
                    eu_tax_rate_determination: str | None = None,
                    alternate_taxation: str | None = None,
                    issue_p_l: int | None = None,
                    function_complement_p_l: str | None = None,
                    bu_49_main_function_type: int | None = None,
                    bu_49_main_function_number: int | None = None,
                    bu_49_function_complement: int | None = None,
                    additional_info_type_1: str | None = None,
                    additional_info_content_1: str | None = None,
                    additional_info_type_2: str | None = None,
                    additional_info_content_2: str | None = None,
                    additional_info_type_3: str | None = None,
                    additional_info_content_3: str | None = None,
                    additional_info_type_4: str | None = None,
                    additional_info_content_4: str | None = None,
                    additional_info_type_5: str | None = None,
                    additional_info_content_5: str | None = None,
                    additional_info_type_6: str | None = None,
                    additional_info_content_6: str | None = None,
                    additional_info_type_7: str | None = None,
                    additional_info_content_7: str | None = None,
                    additional_info_type_8: str | None = None,
                    additional_info_content_8: str | None = None,
                    additional_info_type_9: str | None = None,
                    additional_info_content_9: str | None = None,
                    additional_info_type_10: str | None = None,
                    additional_info_content_10: str | None = None,
                    additional_info_type_11: str | None = None,
                    additional_info_content_11: str | None = None,
                    additional_info_type_12: str | None = None,
                    additional_info_content_12: str | None = None,
                    additional_info_type_13: str | None = None,
                    additional_info_content_13: str | None = None,
                    additional_info_type_14: str | None = None,
                    additional_info_content_14: str | None = None,
                    additional_info_type_15: str | None = None,
                    additional_info_content_15: str | None = None,
                    additional_info_type_16: str | None = None,
                    additional_info_content_16: str | None = None,
                    additional_info_type_17: str | None = None,
                    additional_info_content_17: str | None = None,
                    additional_info_type_18: str | None = None,
                    additional_info_content_18: str | None = None,
                    additional_info_type_19: str | None = None,
                    additional_info_content_19: str | None = None,
                    additional_info_type_20: str | None = None,
                    additional_info_content_20: str | None = None,
                    quantity: int | None = None,
                    weight: Decimal | None = None,
                    payment_method: int | None = None,
                    claim_type: str | None = None,
                    assessment_year: str | None = None,
                    associated_due_date: str | None = None,
                    discount_type: int | None = None,
                    order_number: str | None = None,
                    booking_type: str | None = None,
                    vat_key_installments: int | None = None,
                    eu_member_state_installments: str | None = None,
                    issue_p_l_installments: int | None = None,
                    eu_tax_rate_installments: float | None = None,
                    revenue_account_installments: str | None = None,
                    source_code: str | None = None,
                    cost_center_date: str | None = None,
                    sepa_mandate_reference: str | None = None,
                    discount_lock: int | None = None,
                    shareholder_name: str | None = None,
                    participant_number: int | None = None,
                    identification_number: str | None = None,
                    signatory_number: str | None = None,
                    post_block_until: str | None = None,
                    designation_sobil_issue: str | None = None,
                    indicator_sobil_booking: int | None = None,
                    fixation: int | None = None,
                    performance_date: str | None = None,
                    date_assign_tax_period: str | None = None,
                    due_date: str | None = None,
                    general_reverse: str | None = None,
                    tax_rate: Decimal | None = None,
                    country: str | None = None,
                    billing_reference: str | None = None,
                    bvv_position: int | None = None,
                    eu_member_state_and_vat_id_origin: str | None = None,
                    eu_tax_rate_origin: str | None = None):
        """
        Add a booking to the file.

        :param revenue: Revenue (field #1)
            Revenue/amount for the dataset, e.g., 1234567890.12 Amount must be positive.
        :param debit_credit_indicator: Debit/Credit Indicator (field #2)
            Debit/Credit indicator refers to field #7 Account. S = Debit (default), H = Credit
        :param currency_code_revenue: Currency Code Revenue (field #3)
            ISO code of the currency #22 from the header = default. List of ISO codes.
        :param exchange_rate: Exchange Rate (field #4)
            If revenue is stated in foreign currency in #1, #004, #005, and #006 must be provided, e.g., 1234.123456.
        :param base_revenue: Base Revenue (field #5)
            See #004, e.g., 1234567890.12.
        :param currency_code_base_revenue: Currency Code Base Revenue (field #6)
            See #004. List of ISO codes.
        :param account: Account (field #7)
            Asset or personal account, e.g., 8400.
        :param contra_account_without_bu_key: Contra Account (without BU key) (field #8)
            Asset or personal account, e.g., 70000.
        :param bu_key: Business Unit Key (field #9)
            Control code for mapping different functions/scenarios. Further details.
        :param document_date: Document Date (field #10)
            Format: DDMM, e.g., 0105. The year is always determined from field 13 of the header.
        :param document_field_1: Document Field 1 (field #11)
            Invoice/document number used as a "key" for offsetting open invoices, e.g., "Rg32029/2019". Special characters: $ & % * + - / Other characters are not allowed (especially spaces, umlauts, period, comma, semicolon, and colon).
        :param document_field_2: Document Field 2 (field #12)
            Multiple functions. Details see here.
        :param discount: Discount (field #13)
            Discount amount, e.g., 3.71, only allowed for payment transactions.
        :param posting_text: Posting Text (field #14)
            0-60 characters.
        :param item_block: Item Block (field #15)
            Reminder or payment block. 0 = no block (default), 1 = block. The invoice can be excluded from the dunning/payment proposal.
        :param miscellaneous_address_number: Miscellaneous Address Number (field #16)
            Address number of a miscellaneous address. #OPOS
        :param business_partner_bank: Business Partner Bank (field #17)
            Reference to use a specific business partner bank for direct debit or payment. #OPOS The SEPA mandate reference field (field #105) must be filled when importing the business partner bank.
        :param issue: Issue (field #18)
            Indicator for a reminder interest/fee record. 31 = Reminder interest, 40 = Reminder fee. #OPOS
        :param interest_lock: Interest Lock (field #19)
            Lock for reminder interests. 0 = no lock (default), 1 = lock. #OPOS
        :param document_link: Document Link (field #20)
            Link to a digital document in a DATEV app. BEDI = Unternehmen online. The document link consists of a program abbreviation and the GUID. Since the document link is a text field, the quotation marks must be doubled in the interface file, e.g., "BEDI "f9a0475d-d0df…"
        :param document_info_type_1: Document Info Type 1 (field #21)
            In a DATEV format created from a DATEV accounting program, these fields can contain information from a document (e.g., an electronic bank transaction). If the length of a document info content field is exceeded, the information continues in the next document info field. Important note: A document info always consists of the components document info type and document info content. If you want to use the document info, please fill both fields. Example: Document Info Type: Bank Transactions of the respective bank Document Info Content: Booking-specific contents for the above-mentioned types of information.
        :param document_info_content_1: Document Info Content 1 (field #22)
            See #21.
        :param document_info_type_2: Document Info Type 2 (field #23)
            See #21.
        :param document_info_content_2: Document Info Content 2 (field #24)
            See #21.
        :param document_info_type_3: Document Info Type 3 (field #25)
            See #21.
        :param document_info_content_3: Document Info Content 3 (field #26)
            See #21.
        :param document_info_type_4: Document Info Type 4 (field #27)
            See #21.
        :param document_info_content_4: Document Info Content 4 (field #28)
            See #21.
        :param document_info_type_5: Document Info Type 5 (field #29)
            See #21.
        :param document_info_content_5: Document Info Content 5 (field #30)
            See #21.
        :param document_info_type_6: Document Info Type 6 (field #31)
            See #21.
        :param document_info_content_6: Document Info Content 6 (field #32)
            See #21.
        :param document_info_type_7: Document Info Type 7 (field #33)
            See #21.
        :param document_info_content_7: Document Info Content 7 (field #34)
            See #21.
        :param document_info_type_8: Document Info Type 8 (field #35)
            See #21.
        :param document_info_content_8: Document Info Content 8 (field #36)
            See #21.
        :param cost_center_1: Cost Center 1 (field #37)
            Allocation of the business transaction for subsequent cost accounting via KOST1. The used length must be set in the master data by the KOST program.
        :param cost_center_2: Cost Center 2 (field #38)
            Allocation of the business transaction for subsequent cost accounting via KOST2. The used length must be set in the master data by the KOST program.
        :param cost_quantity: Cost Quantity (field #39)
            The cost quantity field captures the value to a specific reference size for a cost center. This reference size can be e.g., kg, g, cm, m, %. The reference size is defined in the cost accounting master data. Example: 123123123.1234
        :param eu_member_state_and_vat_id_determination: EU Member State and VAT ID (Determination) (field #40)
            The VAT ID number consists of - 2-digit country code (see Doc No. 1080169; Exception: Greece and Northern Ireland, country codes are EL for Greece and XI for Northern Ireland) - 13-digit VAT ID number - Example: DE133546770. The VAT ID number can also contain letters, e.g., for Austria. Detailed information on capturing EU information in the booking record: Doc No. 9211462.
        :param eu_tax_rate_determination: EU Tax Rate (Determination) (field #41)
            Only for corresponding EU bookings: The valid tax rate in the EU destination country. Example: 12.12
        :param alternate_taxation: Alternate Taxation Method (field #42)
            For bookings that should be processed using a different VAT rate than the one in the client master data, the alternate taxation method can be provided in the booking record: I = Accrual basis taxation, K = No VAT invoice, P = Flat rate (e.g., for agriculture and forestry), S = Cash basis taxation
        :param issue_p_l: Issue L+L (field #43)
            Issues according to § 13b (1) sentence 1 No. 1-5 UStG. Note: The value 0 is not allowed. Issue number see Info-Doc 1034915.
        :param function_complement_p_l: Function Complement L+L (field #44)
            Tax rate / function for the L+L issue. Note: The value 0 is not allowed. Example: Value 190 for 19%.
        :param bu_49_main_function_type: BU 49 Main Function Type (field #45)
            When using the BU key 49 for "other tax rates," the tax issue must be provided.
        :param bu_49_main_function_number: BU 49 Main Function Number (field #46)
            See #45.
        :param bu_49_function_complement: BU 49 Function Complement (field #47)
            See #45.
        :param additional_info_type_1: Additional Information - Type 1 (field #48)
            Additional information that can be captured for booking records. These additional pieces of information function as a note and can be entered freely. Important note: Additional information always consists of the components information type and information content. If you want to use additional information, please fill both fields. Example: Information type, e.g., branch or size (sqm). Information content: Booking-specific contents for the above-mentioned types of information.
        :param additional_info_content_1: Additional Information - Content 1 (field #49)
            See #48.
        :param additional_info_type_2: Additional Information - Type 2 (field #50)
            See #48.
        :param additional_info_content_2: Additional Information - Content 2 (field #51)
            See #48.
        :param additional_info_type_3: Additional Information - Type 3 (field #52)
            See #48.
        :param additional_info_content_3: Additional Information - Content 3 (field #53)
            See #48.
        :param additional_info_type_4: Additional Information - Type 4 (field #54)
            See #48.
        :param additional_info_content_4: Additional Information - Content 4 (field #55)
            See #48.
        :param additional_info_type_5: Additional Information - Type 5 (field #56)
            See #48.
        :param additional_info_content_5: Additional Information - Content 5 (field #57)
            See #48.
        :param additional_info_type_6: Additional Information - Type 6 (field #58)
            See #48.
        :param additional_info_content_6: Additional Information - Content 6 (field #59)
            See #48.
        :param additional_info_type_7: Additional Information - Type 7 (field #60)
            See #48.
        :param additional_info_content_7: Additional Information - Content 7 (field #61)
            See #48.
        :param additional_info_type_8: Additional Information - Type 8 (field #62)
            See #48.
        :param additional_info_content_8: Additional Information - Content 8 (field #63)
            See #48.
        :param additional_info_type_9: Additional Information - Type 9 (field #64)
            See #48.
        :param additional_info_content_9: Additional Information - Content 9 (field #65)
            See #48.
        :param additional_info_type_10: Additional Information - Type 10 (field #66)
            See #48.
        :param additional_info_content_10: Additional Information - Content 10 (field #67)
            See #48.
        :param additional_info_type_11: Additional Information - Type 11 (field #68)
            See #48.
        :param additional_info_content_11: Additional Information - Content 11 (field #69)
            See #48.
        :param additional_info_type_12: Additional Information - Type 12 (field #70)
            See #48.
        :param additional_info_content_12: Additional Information - Content 12 (field #71)
            See #48.
        :param additional_info_type_13: Additional Information - Type 13 (field #72)
            See #48.
        :param additional_info_content_13: Additional Information - Content 13 (field #73)
            See #48.
        :param additional_info_type_14: Additional Information - Type 14 (field #74)
            See #48.
        :param additional_info_content_14: Additional Information - Content 14 (field #75)
            See #48.
        :param additional_info_type_15: Additional Information - Type 15 (field #76)
            See #48.
        :param additional_info_content_15: Additional Information - Content 15 (field #77)
            See #48.
        :param additional_info_type_16: Additional Information - Type 16 (field #78)
            See #48.
        :param additional_info_content_16: Additional Information - Content 16 (field #79)
            See #48.
        :param additional_info_type_17: Additional Information - Type 17 (field #80)
            See #48.
        :param additional_info_content_17: Additional Information - Content 17 (field #81)
            See #48.
        :param additional_info_type_18: Additional Information - Type 18 (field #82)
            See #48.
        :param additional_info_content_18: Additional Information - Content 18 (field #83)
            See #48.
        :param additional_info_type_19: Additional Information - Type 19 (field #84)
            See #48.
        :param additional_info_content_19: Additional Information - Content 19 (field #85)
            See #48.
        :param additional_info_type_20: Additional Information - Type 20 (field #86)
            See #48.
        :param additional_info_content_20: Additional Information - Content 20 (field #87)
            See #48.
        :param quantity: Pieces (field #88)
            Only relevant for issues with SKR 14 agriculture and forestry; for other SKR, the fields are ignored or exported empty.
        :param weight: Weight (field #89)
            See #88.
        :param payment_method: Payment Method (field #90)
            OPOS information 1 = Direct Debit, 2 = Reminder, 3 = Payment
        :param claim_type: Claim Type (field #91)
            OPOS information
        :param assessment_year: Assessment Year (field #92)
            OPOS information Format: YYYY
        :param associated_due_date: Associated Due Date (field #93)
            OPOS information Format: DDMMYYYY
        :param discount_type: Discount Type (field #94)
            1 = Purchase of goods, 2 = Purchase of raw materials, auxiliary and operating materials
        :param order_number: Order Number (field #95)
            General description of the order/project. The booking type (field 96) must also be provided with the order number.
        :param booking_type: Booking Type (field #96)
            AA = Requested Down Payment/Partial Invoice, AG = Received Down Payment (Receipt of Money), AV = Received Down Payment (Liability), SR = Final Invoice, SU = Final Invoice (Transfer), SG = Final Invoice (Receipt of Money), SO = Other
        :param vat_key_installments: VAT Key (Down Payments) (field #97)
            VAT key of the subsequent final invoice.
        :param eu_member_state_installments: EU Member State (Down Payments) (field #98)
            EU member state of the subsequent final invoice; see Info-Doc 1080169.
        :param issue_p_l_installments: Issue L+L (Down Payments) (field #99)
            L+L issue of the subsequent final invoice. Issues according to § 13b UStG. Note: The value 0 is not allowed. Issue number see Info-Doc 1034915.
        :param eu_tax_rate_installments: EU Tax Rate (Down Payments) (field #100)
            EU tax rate of the subsequent final invoice. Only for corresponding EU bookings: The valid tax rate in the EU destination country. Example: 12.12
        :param revenue_account_installments: Revenue Account (Down Payments) (field #101)
            Revenue account of the subsequent final invoice.
        :param source_code: Source Code (field #102)
            Replaced by SV (batch processing) during import.
        :param cost_center_date: Cost Center Date (field #104)
            Format DDMMYYYY
        :param sepa_mandate_reference: SEPA Mandate Reference (field #105)
            Individually assigned identifier of a mandate (e.g., invoice or customer number) by the payee. When importing the SEPA mandate reference, the field "Business Partner Bank" (field #17) must also be filled.
        :param discount_lock: Discount Lock (field #106)
            Valid values: 0, 1. 1 = Discount lock, 0 = No discount lock.
        :param shareholder_name: Shareholder Name (field #107)

        :param participant_number: Participant Number (field #108)
            The participant number must correspond to the official number from the tax return and must not be arbitrarily assigned. Maintenance of shareholder data and the creation of special balance sheet issues is only possible in consultation with the tax consultancy. Relates to fields 107-110.
        :param identification_number: Identification Number (field #109)

        :param signatory_number: Signatory Number (field #110)

        :param post_block_until: Post Block Until (field #111)
            Format DDMMYYYY
        :param designation_sobil_issue: Designation SoBil Issue (field #112)

        :param indicator_sobil_booking: Indicator SoBil Booking (field #113)
            SoBil booking generated = 1 SoBil booking not generated = (Default) or 0
        :param fixation: Fixation (field #114)
            Empty = not defined; automatically fixed 0 = no fixation 1 = fixation If a booking record in this field has the content 1, the entire batch will be fixed after import.
        :param performance_date: Performance Date (field #115)
            Format DDMMYYYY; see Info-Doc 9211426. When importing the performance date, the field "116 Date Assign Tax Period" must be filled. The use of the performance date must be coordinated with the tax advisor.
        :param date_assign_tax_period: Date Assign Tax Period (field #116)
            Format DDMMYYYY
        :param due_date: Due Date (field #117)
            OPOS information, format: DDMMYYYY. OPOS processing information via document field 2 (field number 12) is not usable in this case.
        :param general_reverse: General Reverse (field #118)
            G or 1 = General Reverse, 0 = No general reverse.
        :param tax_rate: Tax Rate (field #119)
            Required when using BU keys without a fixed tax rate (e.g., BU key 100). Further information under Doc. No. 9231347, chapter "Entering a tax rate for tax keys."
        :param country: Country (field #120)
            Example: DE for Germany
        :param billing_reference: Billing Reference (field #121)
            The billing reference represents an aggregation of all transactions of the payment service provider and the associated payout. It is provided via the payment data service and taken into account when generating booking proposals.
        :param bvv_position: BVV Position (Operating Asset Comparison) (field #122)
            Details for the field can be found here. 1 Capital adjustment, 2 Withdrawal/distribution current fiscal year, 3 Contribution/capital increase current fiscal year, 4 Transfer § 6b reserve, 5 Transfer (no assignment)
        :param eu_member_state_and_vat_id_origin: EU Member State and VAT ID (Origin) (field #123)
            The VAT ID consists of - 2-digit country code (see Doc. No. 1080169) Exception Greece: The country code is EL) - 13-digit VAT ID Example: DE133546770. The VAT ID can also contain letters, e.g., for Austria. Detailed information on capturing EU information in booking records: Doc. No: 9211462.
        :param eu_tax_rate_origin: EU Tax Rate (Origin) (field #124)
            Only for corresponding EU bookings: The valid tax rate in the EU origin country. Example: 12.12.
        """

        if len(posting_text) > 60:
            raise ValueError(f"Field `posting_text` may not be longer than 60 characters: \"{posting_text}\"")

        row = [revenue, debit_credit_indicator, currency_code_revenue, exchange_rate, base_revenue,
               currency_code_base_revenue, account, contra_account_without_bu_key, bu_key, datev_date(document_date, short=True),
               document_field_1, document_field_2, discount, posting_text, item_block, miscellaneous_address_number,
               business_partner_bank, issue, interest_lock, document_link, document_info_type_1,
               document_info_content_1, document_info_type_2, document_info_content_2, document_info_type_3,
               document_info_content_3, document_info_type_4, document_info_content_4, document_info_type_5,
               document_info_content_5, document_info_type_6, document_info_content_6, document_info_type_7,
               document_info_content_7, document_info_type_8, document_info_content_8, cost_center_1, cost_center_2,
               cost_quantity, eu_member_state_and_vat_id_determination, eu_tax_rate_determination, alternate_taxation,
               issue_p_l, function_complement_p_l, bu_49_main_function_type, bu_49_main_function_number,
               bu_49_function_complement, additional_info_type_1, additional_info_content_1, additional_info_type_2,
               additional_info_content_2, additional_info_type_3, additional_info_content_3, additional_info_type_4,
               additional_info_content_4, additional_info_type_5, additional_info_content_5, additional_info_type_6,
               additional_info_content_6, additional_info_type_7, additional_info_content_7, additional_info_type_8,
               additional_info_content_8, additional_info_type_9, additional_info_content_9, additional_info_type_10,
               additional_info_content_10, additional_info_type_11, additional_info_content_11, additional_info_type_12,
               additional_info_content_12, additional_info_type_13, additional_info_content_13, additional_info_type_14,
               additional_info_content_14, additional_info_type_15, additional_info_content_15, additional_info_type_16,
               additional_info_content_16, additional_info_type_17, additional_info_content_17, additional_info_type_18,
               additional_info_content_18, additional_info_type_19, additional_info_content_19, additional_info_type_20,
               additional_info_content_20, quantity, weight, payment_method, claim_type, assessment_year,
               associated_due_date, discount_type, order_number, booking_type, vat_key_installments,
               eu_member_state_installments, issue_p_l_installments, eu_tax_rate_installments,
               revenue_account_installments, source_code, "", cost_center_date, sepa_mandate_reference,  # The empty string denotes field #103, which is en empty field used by DATEV
               discount_lock, shareholder_name, participant_number, identification_number, signatory_number,
               post_block_until, designation_sobil_issue, indicator_sobil_booking, fixation, performance_date,
               date_assign_tax_period, due_date, general_reverse, tax_rate, country, billing_reference, bvv_position,
               eu_member_state_and_vat_id_origin, eu_tax_rate_origin]

        self.rows.append(row)

    def add_booking_original_datev_argnames(self, /,
                                            umsatz: Decimal,
                                            soll_haben_kennzeichen: str,
                                            konto: int,
                                            gegenkonto_ohne_bu_schluessel: int,
                                            belegdatum: AnyDateRepresentation,
                                            buchungstext: str,
                                            wkz_umsatz: str = 'EUR',
                                            kurs: Decimal | None = None,
                                            basisumsatz: Decimal | None = None,
                                            wkz_basisumsatz: Decimal | None = None,
                                            bu_schluessel: str | None = None,
                                            belegfeld_1: str | None = None,
                                            belegfeld_2: str | None = None,
                                            skonto: Decimal | None = None,
                                            postensperre: int = 0,
                                            diverse_adressnummer: str | None = None,
                                            geschaeftspartnerbank: int | None = None,
                                            sachverhalt: int | None = None,
                                            zinssperre: int | None = None,
                                            beleglink: str | None = None,
                                            beleginfo_art_1: str | None = None,
                                            beleginfo_inhalt_1: str | None = None,
                                            beleginfo_art_2: str | None = None,
                                            beleginfo_inhalt_2: str | None = None,
                                            beleginfo_art_3: str | None = None,
                                            beleginfo_inhalt_3: str | None = None,
                                            beleginfo_art_4: str | None = None,
                                            beleginfo_inhalt_4: str | None = None,
                                            beleginfo_art_5: str | None = None,
                                            beleginfo_inhalt_5: str | None = None,
                                            beleginfo_art_6: str | None = None,
                                            beleginfo_inhalt_6: str | None = None,
                                            beleginfo_art_7: str | None = None,
                                            beleginfo_inhalt_7: str | None = None,
                                            beleginfo_art_8: str | None = None,
                                            beleginfo_inhalt_8: str | None = None,
                                            kost1_kostenstelle: str | None = None,
                                            kost2_kostenstelle: str | None = None,
                                            kost_menge: str | None = None,
                                            eu_mitgliedstaat_ustid_bestimmung: str | None = None,
                                            eu_steuersatz_bestimmung: str | None = None,
                                            abw_versteuerungsart: str | None = None,
                                            sachverhalt_l_l: int | None = None,
                                            funktionsergaenzung_l_l: str | None = None,
                                            bu_49_hauptfunktiontyp: int | None = None,
                                            bu_49_hauptfunktionsnummer: int | None = None,
                                            bu_49_funktionsergaenzung: int | None = None,
                                            zusatzinformation_art_1: str | None = None,
                                            zusatzinformation_inhalt_1: str | None = None,
                                            zusatzinformation_art_2: str | None = None,
                                            zusatzinformation_inhalt_2: str | None = None,
                                            zusatzinformation_art_3: str | None = None,
                                            zusatzinformation_inhalt_3: str | None = None,
                                            zusatzinformation_art_4: str | None = None,
                                            zusatzinformation_inhalt_4: str | None = None,
                                            zusatzinformation_art_5: str | None = None,
                                            zusatzinformation_inhalt_5: str | None = None,
                                            zusatzinformation_art_6: str | None = None,
                                            zusatzinformation_inhalt_6: str | None = None,
                                            zusatzinformation_art_7: str | None = None,
                                            zusatzinformation_inhalt_7: str | None = None,
                                            zusatzinformation_art_8: str | None = None,
                                            zusatzinformation_inhalt_8: str | None = None,
                                            zusatzinformation_art_9: str | None = None,
                                            zusatzinformation_inhalt_9: str | None = None,
                                            zusatzinformation_art_10: str | None = None,
                                            zusatzinformation_inhalt_10: str | None = None,
                                            zusatzinformation_art_11: str | None = None,
                                            zusatzinformation_inhalt_11: str | None = None,
                                            zusatzinformation_art_12: str | None = None,
                                            zusatzinformation_inhalt_12: str | None = None,
                                            zusatzinformation_art_13: str | None = None,
                                            zusatzinformation_inhalt_13: str | None = None,
                                            zusatzinformation_art_14: str | None = None,
                                            zusatzinformation_inhalt_14: str | None = None,
                                            zusatzinformation_art_15: str | None = None,
                                            zusatzinformation_inhalt_15: str | None = None,
                                            zusatzinformation_art_16: str | None = None,
                                            zusatzinformation_inhalt_16: str | None = None,
                                            zusatzinformation_art_17: str | None = None,
                                            zusatzinformation_inhalt_17: str | None = None,
                                            zusatzinformation_art_18: str | None = None,
                                            zusatzinformation_inhalt_18: str | None = None,
                                            zusatzinformation_art_19: str | None = None,
                                            zusatzinformation_inhalt_19: str | None = None,
                                            zusatzinformation_art_20: str | None = None,
                                            zusatzinformation_inhalt_20: str | None = None,
                                            stueck: int | None = None,
                                            gewicht: Decimal | None = None,
                                            zahlweise: int | None = None,
                                            forderungsart: str | None = None,
                                            veranlagungsjahr: str | None = None,
                                            zugeordnete_faelligkeit: str | None = None,
                                            skontotyp: int | None = None,
                                            auftragsnummer: str | None = None,
                                            buchungstyp: str | None = None,
                                            ust_schluessel_anzahlungen: int | None = None,
                                            eu_mitgliedstaat_anzahlungen: str | None = None,
                                            sachverhalt_l_l_anzahlungen: int | None = None,
                                            eu_steuersatz_anzahlungen: float | None = None,
                                            erloeskonto_anzahlungen: str | None = None,
                                            herkunft_kz: str | None = None,
                                            kost_datum: str | None = None,
                                            sepa_mandatsreferenz: str | None = None,
                                            skontosperre: int | None = None,
                                            gesellschaftername: str | None = None,
                                            beteiligtennummer: int | None = None,
                                            identifikationsnummer: str | None = None,
                                            zeichnernummer: str | None = None,
                                            postensperre_bis: str | None = None,
                                            bezeichnung_sobil_sachverhalt: str | None = None,
                                            kennzeichen_sobil_buchung: int | None = None,
                                            festschreibung: int | None = None,
                                            leistungsdatum: str | None = None,
                                            datum_zuord_steuerperiode: str | None = None,
                                            faelligkeit: str | None = None,
                                            generalumkehr: str | None = None,
                                            steuersatz: Decimal | None = None,
                                            land: str | None = None,
                                            abrechnungsreferenz: str | None = None,
                                            bvv_position_betriebsvermoegensvergleich: int | None = None,
                                            eu_mitgliedstaat_ustid_ursprung: str | None = None,
                                            eu_steuersatz_ursprung: str | None = None):
        """
        Add a booking. This method is similar to `add_booking` except that the argument names are the
        original german DATEV field names (see https://apps.datev.de/help-center/documents/1036228).

        :param umsatz: Umsatz (Feld #1)
            Umsatz/Betrag für den Datensatz z.B.: 1234567890,12 Betrag muss positiv sein.
        :param soll_haben_kennzeichen: Soll-/Haben-Kennzeichen (Feld #2)
            Soll-/Haben-Kennzeichnung bezieht sich auf das Feld #7 Konto S = SOLL (default) H = HABEN
        :param wkz_umsatz: WKZ Umsatz (Feld #3)
            ISO-Code der Währung #22 aus Header = default Liste der ISO-Codes
        :param kurs: Kurs (Feld #4)
            Wenn Umsatz in Fremdwährung bei #1 angegeben wird #004, 005 und 006 sind zu übergeben z.B.: 1234,123456
        :param basisumsatz: Basisumsatz (Feld #5)
            Siehe #004. z.B.: 1234567890,12
        :param wkz_basisumsatz: WKZ Basisumsatz (Feld #6)
            Siehe #004. Liste der ISO-Codes
        :param konto: Konto (Feld #7)
            Sach- oder Personenkonto z.B. 8400
        :param gegenkonto_ohne_bu_schluessel: Gegenkonto (ohne BU-Schlüssel) (Feld #8)
            Sach- oder Personenkonto z.B. 70000
        :param bu_schluessel: BU-Schlüssel (Feld #9)
            Steuerungskennzeichen zur Abbildung verschiedener Funktionen/Sachverhalte Weitere Details
        :param belegdatum: Belegdatum (Feld #10)
            Format: TTMM, z.B. 0105 Das Jahr wird immer aus dem Feld 13 des Headers ermittelt
        :param belegfeld_1: Belegfeld 1 (Feld #11)
            Rechnungs-/Belegnummer Wird als "Schlüssel" für den Ausgleich offener Rechnungen genutzt z.B. "Rg32029/2019" Sonderzeichen: $ & % * + - / Andere Zeichen sind unzulässig (insbesondere Leerzeichen, Umlaute, Punkt, Komma, Semikolon und Doppelpunkt).
        :param belegfeld_2: Belegfeld 2 (Feld #12)
            Mehrere Funktionen Details siehe hier
        :param skonto: Skonto (Feld #13)
            Skontobetrag z.B. 3,71 nur bei Zahlungsbuchungen zulässig
        :param buchungstext: Buchungstext (Feld #14)
            0-60 Zeichen
        :param postensperre: Postensperre (Feld #15)
            Mahn- oder Zahlsperre 0 = keine Sperre (default) 1 = Sperre Die Rechnung kann aus dem Mahnwesen / Zahlungsvorschlag ausgeschlossen werden.
        :param diverse_adressnummer: Diverse Adressnummer (Feld #16)
            Adressnummer einer diversen Adresse. #OPOS
        :param geschaeftspartnerbank: Geschäftspartnerbank (Feld #17)
            Referenz um für Lastschrift oder Zahlung eine bestimmte Geschäftspartnerbank genutzt werden soll. #OPOS Beim Import der Geschäftspartnerbank muss auch das Feld SEPA-Mandatsreferenz (Feld-Nr. 105) gefüllt sein.
        :param sachverhalt: Sachverhalt (Feld #18)
            Kennzeichen für einen Mahnzins/Mahngebühr-Datensatz 31 = Mahnzins 40 = Mahngebühr #OPOS
        :param zinssperre: Zinssperre (Feld #19)
            Sperre für Mahnzinsen 0 = keine Sperre (default) 1 = Sperre #OPOS
        :param beleglink: Beleglink (Feld #20)
            Link zu einem digitalen Beleg in einer DATEV App. BEDI = Unternehmen online Der Beleglink besteht aus einem Programmkürzel und der GUID. Da das Feld Beleglink ein Textfeld ist, müssen in der Schnittstellendatei die Anführungszeichen verdoppelt werden. z.B. "BEDI "f9a0475d-d0df…"
        :param beleginfo_art_1: Beleginfo -Art 1 (Feld #21)
            Bei einem DATEV-Format, das aus einem DATEV-Rechnungswesen-Programm erstellt wurde, können diese Felder Informationen aus einem Beleg (z. B. einem elektronischen Kontoumsatz) enthalten. Wird die Feldlänge eines Beleginfo-Inhalts-Feldes überschrit- ten, wird die Information im nächsten Beleginfo-Feld weitergeführt. Wichtiger Hinweis Eine Beleginfo besteht immer aus den Bestandteilen Beleginfo-Art und Beleginfo-Inhalt. Wenn Sie die Beleginfo nutzen möchten, füllen Sie bitte immer beide Felder. Beispiel: Beleginfo-Art: Kontoumsätze der jeweiligen Bank Beleginfo-Inhalt: Buchungsspezifische Inhalte zu den oben genannten Informationsarten
        :param beleginfo_inhalt_1: Beleginfo -Inhalt 1 (Feld #22)
            siehe #21
        :param beleginfo_art_2: Beleginfo -Art 2 (Feld #23)
            siehe #21
        :param beleginfo_inhalt_2: Beleginfo -Inhalt 2 (Feld #24)
            siehe #21
        :param beleginfo_art_3: Beleginfo -Art 3 (Feld #25)
            siehe #21
        :param beleginfo_inhalt_3: Beleginfo -Inhalt 3 (Feld #26)
            siehe #21
        :param beleginfo_art_4: Beleginfo -Art 4 (Feld #27)
            siehe #21
        :param beleginfo_inhalt_4: Beleginfo -Inhalt 4 (Feld #28)
            siehe #21
        :param beleginfo_art_5: Beleginfo -Art 5 (Feld #29)
            siehe #21
        :param beleginfo_inhalt_5: Beleginfo -Inhalt 5 (Feld #30)
            siehe #21
        :param beleginfo_art_6: Beleginfo -Art 6 (Feld #31)
            siehe #21
        :param beleginfo_inhalt_6: Beleginfo -Inhalt 6 (Feld #32)
            siehe #21
        :param beleginfo_art_7: Beleginfo -Art 7 (Feld #33)
            siehe #21
        :param beleginfo_inhalt_7: Beleginfo -Inhalt 7 (Feld #34)
            siehe #21
        :param beleginfo_art_8: Beleginfo -Art 8 (Feld #35)
            siehe #21
        :param beleginfo_inhalt_8: Beleginfo -Inhalt 8 (Feld #36)
            siehe #21
        :param kost1_kostenstelle: KOST1 -Kostenstelle (Feld #37)
            Über KOST1 erfolgt die Zuordnung des Geschäftsvorfalls für die anschließende Kostenrechnung. Die benutzte Länge muss vorher in den Stammdaten vom KOST-Programm eingestellt werden.
        :param kost2_kostenstelle: KOST2 -Kostenstelle (Feld #38)
            Über KOST2 erfolgt die Zuordnung des Geschäftsvorfalls für die anschließende Kostenrechnung. Die benutzte Länge muss vorher in den Stammdaten vom KOST-Programm eingestellt werden.
        :param kost_menge: KOST-Menge (Feld #39)
            Im KOST-Mengenfeld wird die Wertgabe zu einer bestimmten Bezugsgröße für eine Kostenstelle erfasst. Diese Bezugsgröße kann z. B. kg, g, cm, m, % sein. Die Bezugsgröße ist definiert in den Kostenrechnungs-Stammdaten. Beispiel:123123123,1234
        :param eu_mitgliedstaat_ustid_bestimmung: EU-Mitgliedstaat u. UStID (Bestimmung) (Feld #40)
            Die USt-IdNr. besteht aus  - 2-stelligen Länderkürzel (siehe Dok.-Nr. 1080169; Ausnahme Griechenland und Nordirland: Das Länderkürzel lautet EL für Griechenland und XI für Nordirland)  - 13-stelliger USt-IdNr.  - Beispiel: DE133546770. Die USt-IdNr kann auch Buchstaben haben, z.B.: bei Österreich Detaillierte Informationen zur Erfassung von EU-Informationen im Buchungssatz: Dok.-Nr: 9211462.
        :param eu_steuersatz_bestimmung: EU-Steuersatz (Bestimmung) (Feld #41)
            Nur für entsprechende EU-Buchungen: Der im EU-Bestimmungsland gültige Steuersatz. Beispiel: 12,12
        :param abw_versteuerungsart: Abw. Versteuerungsart (Feld #42)
            Für Buchungen, die in einer von der Mandantenstammdaten- Schlüsselung abweichenden Umsatzsteuerart verarbeitet werden sollen, kann die abweichende Versteuerungsart im Buchungssatz übergeben werden: I = Ist-Versteuerung K = keine Umsatzsteuerrechnung P = Pauschalierung (z. B. für Land- und Forstwirtschaft) S = Soll-Versteuerung
        :param sachverhalt_l_l: Sachverhalt L+L (Feld #43)
            Sachverhalte gem. § 13b Abs. 1 Satz 1 Nrn. 1.-5. UStG Achtung: Der Wert 0 ist unzulässig. Sachverhalts-Nummer siehe Info-Doku 1034915
        :param funktionsergaenzung_l_l: Funktionsergänzung L+L (Feld #44)
            Steuersatz / Funktion zum L+L-Sachverhalt Achtung: Der Wert 0 ist unzulässig. Beispiel: Wert 190 für 19%
        :param bu_49_hauptfunktiontyp: BU 49 Hauptfunktiontyp (Feld #45)
            Bei Verwendung des BU-Schlüssels 49 für „andere Steuer- sätze“ muss der steuerliche Sachverhalt mitgegeben werden
        :param bu_49_hauptfunktionsnummer: BU 49 Hauptfunktionsnummer (Feld #46)
            siehe #45
        :param bu_49_funktionsergaenzung: BU 49 Funktionsergänzung (Feld #47)
            siehe #45
        :param zusatzinformation_art_1: Zusatzinformation – Art 1 (Feld #48)
            Zusatzinformationen, die zu Buchungssätzen erfasst werden können. Diese Zusatzinformationen besitzen den Charakter eines Notizzettels und können frei erfasst werden. Wichtiger Hinweis Eine Zusatzinformation besteht immer aus den Bestandtei- len Informationsart und Informationsinhalt. Wenn Sie die Zusatzinformation nutzen möchten, füllen Sie bitte immer beide Felder. Beispiel: Informationsart, z. B. Filiale oder Mengengrößen (qm) Informationsinhalt: buchungsspezifische Inhalte zu den oben genannten Informationsarten.
        :param zusatzinformation_inhalt_1: Zusatzinformation – Inhalt 1 (Feld #49)
            siehe #48
        :param zusatzinformation_art_2: Zusatzinformation – Art 2 (Feld #50)
            siehe #48
        :param zusatzinformation_inhalt_2: Zusatzinformation – Inhalt 2 (Feld #51)
            siehe #48
        :param zusatzinformation_art_3: Zusatzinformation – Art 3 (Feld #52)
            siehe #48
        :param zusatzinformation_inhalt_3: Zusatzinformation – Inhalt 3 (Feld #53)
            siehe #48
        :param zusatzinformation_art_4: Zusatzinformation – Art 4 (Feld #54)
            siehe #48
        :param zusatzinformation_inhalt_4: Zusatzinformation – Inhalt 4 (Feld #55)
            siehe #48
        :param zusatzinformation_art_5: Zusatzinformation – Art 5 (Feld #56)
            siehe #48
        :param zusatzinformation_inhalt_5: Zusatzinformation – Inhalt 5 (Feld #57)
            siehe #48
        :param zusatzinformation_art_6: Zusatzinformation – Art 6 (Feld #58)
            siehe #48
        :param zusatzinformation_inhalt_6: Zusatzinformation – Inhalt 6 (Feld #59)
            siehe #48
        :param zusatzinformation_art_7: Zusatzinformation – Art 7 (Feld #60)
            siehe #48
        :param zusatzinformation_inhalt_7: Zusatzinformation – Inhalt 7 (Feld #61)
            siehe #48
        :param zusatzinformation_art_8: Zusatzinformation – Art 8 (Feld #62)
            siehe #48
        :param zusatzinformation_inhalt_8: Zusatzinformation – Inhalt 8 (Feld #63)
            siehe #48
        :param zusatzinformation_art_9: Zusatzinformation – Art 9 (Feld #64)
            siehe #48
        :param zusatzinformation_inhalt_9: Zusatzinformation – Inhalt 9 (Feld #65)
            siehe #48
        :param zusatzinformation_art_10: Zusatzinformation – Art 10 (Feld #66)
            siehe #48
        :param zusatzinformation_inhalt_10: Zusatzinformation – Inhalt 10 (Feld #67)
            siehe #48
        :param zusatzinformation_art_11: Zusatzinformation – Art 11 (Feld #68)
            siehe #48
        :param zusatzinformation_inhalt_11: Zusatzinformation – Inhalt 11 (Feld #69)
            siehe #48
        :param zusatzinformation_art_12: Zusatzinformation – Art 12 (Feld #70)
            siehe #48
        :param zusatzinformation_inhalt_12: Zusatzinformation – Inhalt 12 (Feld #71)
            siehe #48
        :param zusatzinformation_art_13: Zusatzinformation – Art 13 (Feld #72)
            siehe #48
        :param zusatzinformation_inhalt_13: Zusatzinformation – Inhalt 13 (Feld #73)
            siehe #48
        :param zusatzinformation_art_14: Zusatzinformation – Art 14 (Feld #74)
            siehe #48
        :param zusatzinformation_inhalt_14: Zusatzinformation – Inhalt 14 (Feld #75)
            siehe #48
        :param zusatzinformation_art_15: Zusatzinformation – Art 15 (Feld #76)
            siehe #48
        :param zusatzinformation_inhalt_15: Zusatzinformation – Inhalt 15 (Feld #77)
            siehe #48
        :param zusatzinformation_art_16: Zusatzinformation – Art 16 (Feld #78)
            siehe #48
        :param zusatzinformation_inhalt_16: Zusatzinformation – Inhalt 16 (Feld #79)
            siehe #48
        :param zusatzinformation_art_17: Zusatzinformation – Art 17 (Feld #80)
            siehe #48
        :param zusatzinformation_inhalt_17: Zusatzinformation – Inhalt 17 (Feld #81)
            siehe #48
        :param zusatzinformation_art_18: Zusatzinformation – Art 18 (Feld #82)
            siehe #48
        :param zusatzinformation_inhalt_18: Zusatzinformation – Inhalt 18 (Feld #83)
            siehe #48
        :param zusatzinformation_art_19: Zusatzinformation – Art 19 (Feld #84)
            siehe #48
        :param zusatzinformation_inhalt_19: Zusatzinformation – Inhalt 19 (Feld #85)
            siehe #48
        :param zusatzinformation_art_20: Zusatzinformation – Art 20 (Feld #86)
            siehe #48
        :param zusatzinformation_inhalt_20: Zusatzinformation – Inhalt 20 (Feld #87)
            siehe #48
        :param stueck: Stück (Feld #88)
            Wirkt sich nur bei Sachverhalt mit SKR 14 Land- und Forst- wirtschaft aus, für andere SKR werden die Felder beim Import / Export überlesen bzw. leer exportiert.
        :param gewicht: Gewicht (Feld #89)
            siehe #88
        :param zahlweise: Zahlweise (Feld #90)
            OPOS-Informationen 1 = Lastschrift 2 = Mahnung 3 = Zahlung
        :param forderungsart: Forderungsart (Feld #91)
            OPOS-Informationen
        :param veranlagungsjahr: Veranlagungsjahr (Feld #92)
            OPOS-Informationen Format: JJJJ
        :param zugeordnete_faelligkeit: Zugeordnete Fälligkeit (Feld #93)
            OPOS-Informationen Format: TTMMJJJJ
        :param skontotyp: Skontotyp (Feld #94)
            1 = Einkauf von Waren 2 = Erwerb von Roh-Hilfs- und Betriebsstoffen
        :param auftragsnummer: Auftragsnummer (Feld #95)
            Allgemeine Bezeichnung, des Auftrags / Projekts. Mit der Auftragsnummer muss auch der Buchungstyp (Feld 96) angegeben werden.
        :param buchungstyp: Buchungstyp (Feld #96)
            AA = Angeforderte Anzahlung / Abschlagsrechnung AG = Erhaltene Anzahlung (Geldeingang) AV = Erhaltene Anzahlung (Verbindlichkeit) SR = Schlussrechnung SU = Schlussrechnung (Umbuchung) SG = Schlussrechnung (Geldeingang) SO = Sonstige
        :param ust_schluessel_anzahlungen: USt-Schlüssel (Anzahlungen) (Feld #97)
            USt-Schlüssel der späteren Schlussrechnung
        :param eu_mitgliedstaat_anzahlungen: EU-Mitgliedstaat (Anzahlungen) (Feld #98)
            EU-Mitgliedstaat der späteren Schlussrechnung siehe Info-Doku 1080169
        :param sachverhalt_l_l_anzahlungen: Sachverhalt L+L (Anzahlungen) (Feld #99)
            L+L-Sachverhalt der späteren Schlussrechnung Sachverhalte gem. § 13b UStG Achtung: Der Wert 0 ist unzulässig. Sachverhalts-Nummer siehe Info-Doku 1034915
        :param eu_steuersatz_anzahlungen: EU-Steuersatz (Anzahlungen) (Feld #100)
            EU-Steuersatz der späteren Schlussrechnung Nur für entsprechende EU-Buchungen: Der im EU-Bestimmungsland gültige Steuersatz. Beispiel: 12,12
        :param erloeskonto_anzahlungen: Erlöskonto (Anzahlungen) (Feld #101)
            Erlöskonto der späteren Schlussrechnung
        :param herkunft_kz: Herkunft-Kz (Feld #102)
            Wird beim Import durch SV (Stapelverarbeitung) ersetzt.
        :param kost_datum: KOST-Datum (Feld #104)
            Format TTMMJJJJ
        :param sepa_mandatsreferenz: SEPA-Mandatsreferenz (Feld #105)
            Vom Zahlungsempfänger individuell vergebenes Kennzeichen eines Mandats (z.B. Rechnungs- oder Kundennummer). Beim Import der SEPA-Mandatsreferenz muss auch das Feld Geschäftspartnerbank (Feld-Nr. 17) gefüllt sein.
        :param skontosperre: Skontosperre (Feld #106)
            Gültige Werte: 0, 1. 1 = Skontosperre 0 = Keine Skontosperre
        :param gesellschaftername: Gesellschaftername (Feld #107)

        :param beteiligtennummer: Beteiligtennummer (Feld #108)
            Die Beteiligtennummer muss der amtlichen Nummer aus der Feststellungserklärung entsprechen, diese darf nicht beliebig vergeben werden. Die Pflege der Gesellschafterdaten und das Anlegen von Sonderbilanzsachverhalte ist nur in Absprache mit der Steuerkanzlei möglich. Betrifft Feld 107-110.
        :param identifikationsnummer: Identifikationsnummer (Feld #109)

        :param zeichnernummer: Zeichnernummer (Feld #110)

        :param postensperre_bis: Postensperre bis (Feld #111)
            Format TTMMJJJJ
        :param bezeichnung_sobil_sachverhalt: Bezeichnung SoBil-Sachverhalt (Feld #112)

        :param kennzeichen_sobil_buchung: Kennzeichen SoBil-Buchung (Feld #113)
            Sobil-Buchung erzeugt = 1 Sobil-Buchung nicht erzeugt = (Default) bzw. 0
        :param festschreibung: Festschreibung (Feld #114)
            leer = nicht definiert; wird automatisch festgeschrieben 0 = keine Festschreibung 1 = Festschreibung Hat ein Buchungssatz in diesem Feld den Inhalt 1, so wird der gesamte Stapel nach dem Import festgeschrieben.
        :param leistungsdatum: Leistungsdatum (Feld #115)
            Format TTMMJJJJ siehe Info-Doku 9211426 Beim Import des Leistungsdatums muss das Feld „116 Datum Zuord. Steuer-periode“ gefüllt sein. Der Einsatz des Leistungsdatums muss in Absprache mit dem Steuerberater erfolgen.
        :param datum_zuord_steuerperiode: Datum Zuord. Steuerperiode (Feld #116)
            Format TTMMJJJJ
        :param faelligkeit: Fälligkeit (Feld #117)
            OPOS Informationen, Format: TTMMJJJJ OPOS-Verarbeitungsinformationen über Belegfeld 2 (Feldnummer 12) sind in diesem Fall nicht nutzbar
        :param generalumkehr: Generalumkehr (Feld #118)
            G oder 1 = Generalumkehr 0 = keine Generalumkehr
        :param steuersatz: Steuersatz (Feld #119)
            Wird bei Verwendung von BU-Schlüssel ohne festen Steuersatz benötigt (z. B. BU-Schlüssel 100). Weitere Informationen unter Dok.Nr. 9231347 Kapitel „Erfassung eines Steuersatzes bei Steuerschlüsseln“
        :param land: Land (Feld #120)
            Beispiel: DE für Deutschland
        :param abrechnungsreferenz: Abrechnungsreferenz (Feld #121)
            Die Abrechnungsreferenz stellt eine Klammer über alle Transaktionen des Zahlungsdienstleisters und die dazu gehörige Auszahlung dar. Sie wird über den Zahlungsdatenservice bereitgestellt und bei der Erzeugung von Buchungsvorschläge berücksichtigt.
        :param bvv_position_betriebsvermoegensvergleich: BVV-Position (Betriebsvermögensvergleich) (Feld #122)
            Details zum Feld siehe hier 1 Kapitalanpassung 2 Entnahme / Ausschüttung lfd. WJ 3 Einlage / Kapitalzuführung lfd. WJ 4 Übertragung § 6b Rücklage 5 Umbuchung (keine Zuordnung)
        :param eu_mitgliedstaat_ustid_ursprung: EU-Mitgliedstaat u. UStID (Ursprung) (Feld #123)
            Die USt-IdNr. besteht aus  - 2-stelligen Länderkürzel (siehe Dok.-Nr. 1080169) Ausnahme Griechenland: Das Länderkürzel lautet EL)  - 13-stelliger USt-IdNr.  - Beispiel: DE133546770. Die USt-IdNr kann auch Buchstaben haben, z.B.: bei Österreich Detaillierte Informationen zur Erfassung von EU-Informationen im Buchungssatz: Dok.-Nr: 9211462.
        :param eu_steuersatz_ursprung: EU-Steuersatz (Ursprung) (Feld #124)
            Nur für entsprechende EU-Buchungen: Der im EU-Ursprungsland gültige Steuersatz. Beispiel: 12,12
        """

        if len(buchungstext) > 60:
            raise ValueError(f"Field `buchungstext` may not be longer than 60 characters: \"{buchungstext}\"")

        row = [umsatz, soll_haben_kennzeichen, wkz_umsatz, kurs, basisumsatz, wkz_basisumsatz, konto,
               gegenkonto_ohne_bu_schluessel, bu_schluessel, datev_date(belegdatum, short=True), belegfeld_1, belegfeld_2, skonto,
               buchungstext, postensperre, diverse_adressnummer, geschaeftspartnerbank, sachverhalt, zinssperre,
               beleglink, beleginfo_art_1, beleginfo_inhalt_1, beleginfo_art_2, beleginfo_inhalt_2, beleginfo_art_3,
               beleginfo_inhalt_3, beleginfo_art_4, beleginfo_inhalt_4, beleginfo_art_5, beleginfo_inhalt_5,
               beleginfo_art_6, beleginfo_inhalt_6, beleginfo_art_7, beleginfo_inhalt_7, beleginfo_art_8,
               beleginfo_inhalt_8, kost1_kostenstelle, kost2_kostenstelle, kost_menge,
               eu_mitgliedstaat_ustid_bestimmung, eu_steuersatz_bestimmung, abw_versteuerungsart, sachverhalt_l_l,
               funktionsergaenzung_l_l, bu_49_hauptfunktiontyp, bu_49_hauptfunktionsnummer, bu_49_funktionsergaenzung,
               zusatzinformation_art_1, zusatzinformation_inhalt_1, zusatzinformation_art_2, zusatzinformation_inhalt_2,
               zusatzinformation_art_3, zusatzinformation_inhalt_3, zusatzinformation_art_4, zusatzinformation_inhalt_4,
               zusatzinformation_art_5, zusatzinformation_inhalt_5, zusatzinformation_art_6, zusatzinformation_inhalt_6,
               zusatzinformation_art_7, zusatzinformation_inhalt_7, zusatzinformation_art_8, zusatzinformation_inhalt_8,
               zusatzinformation_art_9, zusatzinformation_inhalt_9, zusatzinformation_art_10,
               zusatzinformation_inhalt_10, zusatzinformation_art_11, zusatzinformation_inhalt_11,
               zusatzinformation_art_12, zusatzinformation_inhalt_12, zusatzinformation_art_13,
               zusatzinformation_inhalt_13, zusatzinformation_art_14, zusatzinformation_inhalt_14,
               zusatzinformation_art_15, zusatzinformation_inhalt_15, zusatzinformation_art_16,
               zusatzinformation_inhalt_16, zusatzinformation_art_17, zusatzinformation_inhalt_17,
               zusatzinformation_art_18, zusatzinformation_inhalt_18, zusatzinformation_art_19,
               zusatzinformation_inhalt_19, zusatzinformation_art_20, zusatzinformation_inhalt_20, stueck, gewicht,
               zahlweise, forderungsart, veranlagungsjahr, zugeordnete_faelligkeit, skontotyp, auftragsnummer,
               buchungstyp, ust_schluessel_anzahlungen, eu_mitgliedstaat_anzahlungen, sachverhalt_l_l_anzahlungen,
               eu_steuersatz_anzahlungen, erloeskonto_anzahlungen, herkunft_kz, "", kost_datum,  # The empty string denotes field #103, which is an empty field ("Leerfeld") used by DATEV
               sepa_mandatsreferenz, skontosperre, gesellschaftername, beteiligtennummer, identifikationsnummer,
               zeichnernummer, postensperre_bis, bezeichnung_sobil_sachverhalt, kennzeichen_sobil_buchung,
               festschreibung, leistungsdatum, datum_zuord_steuerperiode, faelligkeit, generalumkehr, steuersatz, land,
               abrechnungsreferenz, bvv_position_betriebsvermoegensvergleich, eu_mitgliedstaat_ustid_ursprung,
               eu_steuersatz_ursprung]

        self.rows.append(row)

    def to_csv(self, out: 'SupportsWrite[str]') -> str | None:
        """
        Write the so far added bookings and header information into a DATEV-compliant
        bookings CSV file. This function returns the contents of the csv file as a string,
        if possible.

        Note: The file name needs to follow certain criteria in order to be successfully
            imported by DATEV software (see https://developer.datev.de/datev/platform/de/dtvf/einstieg).
            Valid examples are: "EXTF_Buchungsstapel.csv" or "EXTF 700 21 Beispiel-Buchungsstapel.csv".
            Use "get_suggested_filename" to retrieve a valid and fitting filename for a file.

        :param out: If given, this method writes the content to the given output writeable.
            If not, it just returns a string containing the csv data. If a writeable is given
            that supports the `getvalue()` method, the data is returned and written to the
            writeable.
        :return: The csv file contents, unless a writeable is given that does not support
            reading using `output.getvalue()`
        """

        io = out or StringIO()
        writer = DatevCSVWriter(io)

        writer.writerow(self.header)
        writer.writerow(self.title_row)

        rows = list(self.rows)  # copy to avoid mutation

        for i, el in enumerate(rows):
            if el is None:
                rows[i] = ""

        for row in rows:
            writer.writerow(row)

        if hasattr(out, 'getvalue'):
            return io.getvalue()

    def get_suggested_filename(self, title: str | None = None):
        if title:
            return self.header[0] + "_" + title + ".csv"
        return "_".join(str(x) for x in self.header[:4]) + f"_{self.start_date.year}.csv"


def datev_date(x: AnyDateRepresentation, short: bool = False) -> str:
    d = parse_any_date(x)
    if short:
        return f'{d.day:02}{d.month:02}'
    else:
        return f'{d.year}{d.month:02}{d.day:02}'

