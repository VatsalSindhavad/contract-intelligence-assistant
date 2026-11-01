# Concrete train failures

Post-evaluation diagnosis only: no gold data entered inference. Test failures have not been inspected.

## 1. partial_evidence — iteration 22

Query ID: `5aacd88644962ff51293f4cc0ae5f18f1815d9a615908bd8283a990dcf5c4569`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Are there any exceptions to competitive restrictions in this contract?

Returned evidence overlaps the annotated answer but omits part of its span. Longer complete-clause evidence or additional support may help; this is an offset-level diagnosis.

Annotated source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`, offsets `[33572, 34034]`.

Annotated text: save that nothing in this paragraph 13.2 shall prevent you from holding (with the prior written consent of the Company, which shall not be unreasonably delayed or withheld) up to three percent (3%) of the issued equity share capital of any company where those equity shares are listed on a recognised investment exchange (as defined in section 285 of the Financial Services and Markets Act 2000) or traded on the AIM market operated by the London Stock Exchange.

Returned source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`, offsets `[41051, 41562)`.

Returned text: 14.4 For the avoidance of doubt nothing in this paragraph 14 shall prevent you from having any dealings with any Prospective Customer or Restricted Customer in relation to any business which is not Restricted Businesses and which is not competitive with the Restricted Business, nor from continuing to deal with any Prospective Customer or Restricted Customer where you either have a social or business relationship unconnected to the Company and that relationship does not compete with the Restricted Business.

## 2. partial_evidence — iteration 22

Query ID: `13d8e76465cd5d5ff8d880d4fcf36657d918c9f750e2aad64d336b3e99babdc2`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Does this contract include any right of first refusal, right of first offer, or right of first negotiation?

Returned evidence overlaps the annotated answer but omits part of its span. Longer complete-clause evidence or additional support may help; this is an offset-level diagnosis.

Annotated source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`, offsets `[6235, 6531]`.

Annotated text: On or as soon as practicable following the Effective Date, it is intended that you will be granted an option under the Option Plan to acquire 107,417 ordinary shares in the capital of BTL ("Shares") (representing approximately 0.6% of the Company's issued share capital as at the Effective Date).

Returned source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`, offsets `[5600, 6600)`.

Returned text:  the Compensation Committee at the end of each calendar year, against annual corporate and personal performance objectives agreed between you and the Board at the start of each calendar year, with any such bonus being payable in the first quarter of the following year. Qualification for your Annual Performance Bonus will require that you are employed by the Company (and have not served notice of termination of your employment to the Company) on 31 December of the year to which your bonus entitlement applies.

2





4.5 Equity Incentives

BTL has established the Bicycle Therapeutics 2019 Share Option Plan (the "Option Plan").

On or as soon a

## 3. partial_evidence — iteration 22

Query ID: `505f5239e0ca460f383a732198b07e7d4dd7f828487adaaae04dbc49d1ae98c4`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; How is intellectual property ownership assigned in this contract?

Returned evidence overlaps the annotated answer but omits part of its span. Longer complete-clause evidence or additional support may help; this is an offset-level diagnosis.

Annotated source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`, offsets `[44840, 45359]`.

Annotated text: To the extent that such IPRs do not vest automatically in the Company by operation of law, you hereby assign and agree to assign to the Company all of your right, title and interest in any existing and future IPRs which may subsist in any Works for their full term of protection (including any extensions, revivals and renewals) together with the right to sue and claim remedies for past infringement and all materials embodying these rights to the fullest extent permitted by law in any and all countries of the world.

Returned source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`, offsets `[44753, 44833)`.

Returned text: All IPRs subsisting in any Works shall be the exclusive property of the Company.

## 4. wrong_section — iteration 22

Query ID: `83b1521f8cc3a39a206573315d1427eeb6dc73dfd5665fdf5f6c940198943a74`

Consider the Service Agreement between Theravance Biopharma UK Limited and Brett Haumann; What is the expiration date of this contract?

Returned evidence has zero character overlap with the annotated answer; rank/source selection needs review.

Annotated source: `cuad/THERAVANCEBIOPHARMA,INC_05_08_2020-EX-10.2-SERVICE AGREEMENT.txt`, offsets `[4382, 4705]`.

Annotated text: The Executive's employment with the Company will commence on the Commencement Date and shall continue, subject to the remaining terms of this Agreement, until terminated by either party giving the other the following minimum advance written notice: 2.1.1 6 weeks' notice;

2.1.2 such other longer period as required by law.

Returned source: `cuad/THERAVANCEBIOPHARMA,INC_05_08_2020-EX-10.2-SERVICE AGREEMENT.txt`, offsets `[0, 1000)`.

Returned text: Exhibit 10.2

STRICTLY PRIVATE AND CONFIDENTIAL

1 April, 2020

THERAVANCE BIOPHARMA UK LIMITED and BRETT HAUMANN

SERVICE AGREEMENT





THIS AGREEMENT is entered into between the parties on 1 April, 2020.

PARTIES (1) Theravance Biopharma UK Limited is a company registered in the United Kingdom and whose registered office is at 12 New Fetter Lane, London, United Kingdom, EC4A 1JP (the "Employer"); and (2) Brett Haumann of [address removed] (the "Executive").

AGREED TERMS 1. Definitions 1.1 The following terms shall have the following meanings unless the context requires otherwise: "Capacity" means as agent, consultant, director, employee, 

## 5. false_abstention — iteration 22

Query ID: `4e02d75b0e79266af8fbf7f6175f3c121b2f112cc0a85d0643d4971971af2029`

Consider the Service Agreement between Theravance Biopharma UK Limited and Brett Haumann; Is there a covenant not to sue included in this contract?

No gold overlap in the first-stage supplied context; retrieval expansion or routing is needed.

Annotated source: `cuad/THERAVANCEBIOPHARMA,INC_05_08_2020-EX-10.2-SERVICE AGREEMENT.txt`, offsets `[27816, 28397]`.

Annotated text: If the Executive's employment is terminated at any time by reason of any reconstruction or amalgamation of any Group Company, whether by winding up or otherwise, and the Executive is offered employment with any concern or undertaking involved in or resulting from the reconstruction or amalgamation on terms which (considered in their entirety) are no less favourable to any material extent than the terms of this Agreement, the Executive acknowledges and agrees that there shall be no claim against the Company or any undertaking arising out of or connected with such termination.

Returned no evidence.

## 6. wrong_section — iteration 22

Query ID: `652ee16919316a0ee5bbe9dfec5c0ccc2441b1c15ab25d5f55dce26b9e4e66f3`

Consider the Sponsorship Agreement between Excite, Inc. and Vitamin Shoppe Industries Inc. for Promotion on WebCrawler Channels; What is the expiration date of this contract?

Returned evidence has zero character overlap with the annotated answer; rank/source selection needs review.

Annotated source: `cuad/VITAMINSHOPPECOMINC_09_13_1999-EX-10.26-SPONSORSHIP AGREEMENT.txt`, offsets `[33237, 33842]`.

Annotated text: Unless terminated earlier in accordance with the                           specific terms of this Agreement, the term of this                           Agreement will begin on the Launch Date and will not                           end until Excite displays a total of [*****]                           impressions of the Client advertising banners and                           promotional placements on the Excite Network as                           described in this Agreement and pushes [*****]                           emails using the email vehicles specified in Exhibit                           B

Returned source: `cuad/VITAMINSHOPPECOMINC_09_13_1999-EX-10.26-SPONSORSHIP AGREEMENT.txt`, offsets `[33845, 34187)`.

Returned text: Regardless of Excite's actual delivery of                           impressions, the term of this Agreement will not be                           shorter than [*****]  after the Launch Date,                           unless the Agreement is terminated earlier in                           accordance with the specific terms of this Agreement.

## 7. false_abstention — iteration 22

Query ID: `4270fd03eabf8522eaba3d591fd31932b63266c8917c19446052c4ce8e5215d1`

Consider the Intellectual Property Agreement for COVID-19 Treatment Development between Marv Enterprises, LLC, Premier Biomedical, Inc., and Technology Health, Inc.; Does this contract include any revenue or profit-sharing arrangements?

Retrieved context contained some gold overlap, but no evidence was returned.

Annotated source: `cuad/PREMIERBIOMEDICALINC_05_14_2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT.txt`, offsets `[11296, 11663]`.

Annotated text: Royalty payments are payable from THI to Marv Enterprises, LLC and will be in the amount of 5% of the Fair Market Value of:   a. Licensed Product that is sold, leased or put into use by the THI or any Related Companies in the preceding calendar quarter; and   b. any service performed by THI or any Related Companies that directly or indirectly uses Licensed Product.

Returned no evidence.

## 8. wrong_section — iteration 22

Query ID: `e72f339f6de330c207361bc87678c4ff2720c5dfeeafe7f5b61e604f38762512`

Consider the Marketing and Transportation Services Agreement between Purolator Courier Ltd. and Parcelway Courier Systems Canada Ltd. (Dynamex Inc.); Is there a non-compete clause in this contract?

Returned evidence has zero character overlap with the annotated answer; rank/source selection needs review.

Annotated source: `cuad/DYNAMEXINC_06_06_1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT.txt`, offsets `[47554, 47970]`.

Annotated text: In the event this Agreement is terminated pursuant to the provisions of         paragraph 17, then the Party in default shall not enter into an         agreement with any other Party to provide services similar to those         provided herein or to provide its services similar to those provided for         herein without an agreement, for a period of six (6) months from the         effective date of termination.

Returned source: `cuad/DYNAMEXINC_06_06_1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT.txt`, offsets `[43200, 44200)`.

Returned text:    TRADE-MARKS

35.1    Each Party's trade-marks, distinctive colours and designs used in         connection with the Services shall remain at all times during the term         of this Agreement and on the expiration or termination thereof, the         exclusive property of each Party and any benefit associated with such         use shall accrue solely to that Party. Each Party shall use the other         Party's trade-mark, distinctive colours and designs only with the         prior written consent of the other Party and only in connection with the         services provided hereunder.

36.0    LAW OF THE AGREEMENT

36.1    This Agreement sha

## 9. false_abstention — iteration 22

Query ID: `4c60c9594f05cd29a230f0230d458cb5a85ff05e0a8703c08fcf9b50e98155dd`

Consider the Marketing and Transportation Services Agreement between Purolator Courier Ltd. and Parcelway Courier Systems Canada Ltd. (Dynamex Inc.); What are the audit rights under this contract?

No gold overlap in the first-stage supplied context; retrieval expansion or routing is needed.

Annotated source: `cuad/DYNAMEXINC_06_06_1996-EX-10.4-TRANSPORTATION SERVICES AGREEMENT.txt`, offsets `[27110, 27294]`.

Annotated text: Either Party shall have the right to request the other to provide,        through an auditor agreed to by the Parties, validation of the        information and data referred to herein.

Returned no evidence.

## 10. invalid_fallback — iteration 23

Query ID: `f03c96c14eab136aa7e9cf1879c3265c77f7c0a671b4857f2a4ea858d4c70951`

Consider the distribution agreement between NimbleCove Media and BluePeak Distribution; Does the agreement allow sublicensing to third-party platforms?

The output failed validation, so the declared fallback returned original passages for a labeled unanswerable query. Strict formatting plus fallback policy caused this false return.

Returned source: `cuad/DUOSTECHNOLOGIESGROUP,INC_04_21_2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT.txt`, offsets `[36800, 37800)`.

Returned text: nder, in whole or in part,  whether voluntarily or by operation of law, without the prior written consent of the other Party, which consent may be withheld at the other Party's  reasonable business discretion; provided, however, that in connection with a merger, sale or transfer of substantially all of the assets or stock of  one of the Parties that Party may provide for the assignee to be bound by the terms hereof. This Agreement shall inure to the benefit of, and shall  be binding upon, the Parties and their respective successors and permitted assigns.     11.3 Good Faith. The Parties undertake to act in good faith, consistent with their re

Validation error: Empty evidence requires the declared no-answer summary.

## 11. invalid_fallback — iteration 23

Query ID: `8880cd6a3ba0d8e8dd659d556bd66c8cf43d31cacdd1f872c87a815e47383c68`

Consider the sponsorship agreement between LumenHarbor Sports and MapleGate Brands; When does the exclusivity period end?

The output failed validation, so the declared fallback returned original passages for a labeled unanswerable query. Strict formatting plus fallback policy caused this false return.

Returned source: `cuad/VITAMINSHOPPECOMINC_09_13_1999-EX-10.26-SPONSORSHIP AGREEMENT.txt`, offsets `[36800, 37800)`.

Returned text:  delivery goal                           at any time during the Make-Good Period, the term of                           this Agreement will continue and Client shall                           immediately resume payment of the sponsorship and                           advertising fees specified in Section 7.





                                    9    10                             CONFIDENTIAL MATERIALS OMITTED AND FILED SEPARATELY                                     WITH THE SECURITIES AND EXCHANGE COMMISSION.                                                      ASTERISKS DENOTE OMISSIONS.

10.              TRADEMARK OWNERSHIP AND LICENSE


Validation error: Empty evidence requires the declared no-answer summary.

## 12. invalid_fallback — iteration 23

Query ID: `439a5a90540a24fd0f7bd4123caab8c688ed516f768385b7ccf5782c2b99ee06`

Consider the co-branding and services agreement between PrimeCall and DeltaThree; Which clause requires approval before using ChatGPT on customer communications?

The output failed validation, so the declared fallback returned original passages for a labeled unanswerable query. Strict formatting plus fallback policy caused this false return.

Returned source: `cuad/DeltathreeInc_19991102_S-1A_EX-10.19_6227850_EX-10.19_Co-Branding Agreement_ Service Agreement.txt`, offsets `[6400, 7400)`.

Returned text:  shall reimburse PrimeCall for all customer service expenses directly related to users of the Calling Card. Notwithstanding the foregoing, the level of customer service shall be subject to the approval of DeltaThree.

         Section 3.06  [Reporting]. Reporting. On or before the tenth day of each calendar month, PrimeCall shall prepare for DeltaThree a report detailing the total revenues and expenses associated with the sale and use of the Calling Cards in the previous month. In the event that DeltaThree disputes any amounts set forth on the report, DeltaThree shall provide PrimeCall with written notice of such dispute, which notice shall d

Validation error: Empty evidence requires the declared no-answer summary.

