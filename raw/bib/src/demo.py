#!/usr/bin/env python3
"""
Demo Script - Book Digitization Pipeline
=========================================

This script demonstrates the pipeline with sample data,
without requiring an actual PDF file or API key.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.yaml_processor import (
    YAMLProcessor, BookContent, BookMetadata, Chapter, Section
)
from modules.html_generator import HTMLGenerator
from modules.latex_generator import LaTeXGenerator, OutputMode


def create_sample_book() -> BookContent:
    """Create a sample book for demonstration"""

    metadata = BookMetadata(
        title="Saint Paul's Epistle to the Colossians",
        title_cn="圣保罗致歌罗西人书注释",
        author="J. B. Lightfoot",
        author_cn="莱特福特",
        year="1879",
        source="https://archive.org/details/saintpaulsepistl00ligh",
        description="A revised text with introductions, notes and dissertations on the Epistle to the Colossians.",
        description_cn="对歌罗西书的修订文本，包含引言、注释和论文。",
        language="en"
    )

    # Preface
    preface_section = Section(
        id=1,
        en="This commentary on the Epistle to the Colossians is the result of many years of careful study. The Greek text has been thoroughly revised, and the notes aim to explain both the grammatical construction and the theological significance of the Apostle's words.",
        cn="这部歌罗西书注释是多年精心研究的成果。希腊文本经过全面修订，注释旨在解释使徒话语的语法结构和神学意义。"
    )

    # Chapter 1 - Sample sections
    ch1_sections = [
        Section(
            id=1,
            en="Paul, an apostle of Jesus Christ by the will of God, and Timotheus our brother, To the saints and faithful brethren in Christ which are at Colosse: Grace be unto you, and peace, from God our Father and the Lord Jesus Christ.",
            cn="奉神旨意，作基督耶稣使徒的保罗和弟兄提摩太，写信给歌罗西的圣徒，在基督里有忠心的弟兄。愿恩惠、平安从神我们的父归于你们。",
            footnotes=[
                {
                    "marker": "[1]",
                    "content": "保罗在此强调他使徒身份的神圣来源",
                    "original": "Paul emphasizes the divine origin of his apostleship"
                }
            ]
        ),
        Section(
            id=2,
            en="We give thanks to God and the Father of our Lord Jesus Christ, praying always for you, Since we heard of your faith in Christ Jesus, and of the love which ye have to all the saints.",
            cn="我们感谢神、我们主耶稣基督的父，常常为你们祷告，因听见你们在基督耶稣里的信心，并向众圣徒的爱心。"
        ),
        Section(
            id=3,
            en="For the hope which is laid up for you in heaven, whereof ye heard before in the word of the truth of the gospel; Which is come unto you, as it is in all the world; and bringeth forth fruit, as it doth also in you, since the day ye heard of it, and knew the grace of God in truth.",
            cn="是为那给你们存在天上的盼望。这盼望就是你们从前在福音真理的道上所听见的。这福音传到你们那里，也传到普天之下，并且结果增长，如同在你们中间，自从你们听见福音，真知道神恩惠的日子一样。"
        )
    ]

    chapter1 = Chapter(
        chapter_number=1,
        title="Salutation and Thanksgiving",
        title_cn="问候与感恩",
        sections=ch1_sections,
        scripture_text="Παῦλος ἀπόστολος Χριστοῦ Ἰησοῦ διὰ θελήματος θεοῦ καὶ Τιμόθεος ὁ ἀδελφός",
        scripture_translation="Paul, an apostle of Christ Jesus by the will of God, and Timothy our brother"
    )

    # Chapter 2 - Sample sections
    ch2_sections = [
        Section(
            id=4,
            en="For I would that ye knew what great conflict I have for you, and for them at Laodicea, and for as many as have not seen my face in the flesh.",
            cn="我愿意你们知道，我为你们和老底嘉人，并一切没有与我亲自见面的人，是何等的尽心竭力。"
        ),
        Section(
            id=5,
            en="That their hearts might be comforted, being knit together in love, and unto all riches of the full assurance of understanding, to the acknowledgment of the mystery of God, and of the Father, and of Christ.",
            cn="要叫他们的心得安慰，因爱心互相联络，以致丰丰足足在悟性中有充足的信心，使他们真知道神的奥秘，就是基督。"
        )
    ]

    chapter2 = Chapter(
        chapter_number=2,
        title="Warning Against False Teaching",
        title_cn="警戒错误教导",
        sections=ch2_sections,
        scripture_text="Θέλω γὰρ ὑμᾶς εἰδέναι ἡλίκον ἀγῶνα ἔχω ὑπὲρ ὑμῶν",
        scripture_translation="For I want you to know how great a struggle I have for you"
    )

    # Chapter 3 - Sample sections
    ch3_sections = [
        Section(
            id=6,
            en="If ye then be risen with Christ, seek those things which are above, where Christ sitteth on the right hand of God. Set your affection on things above, not on things on the earth.",
            cn="所以，你们若真与基督一同复活，就当求在上面的事，那里有基督坐在神的右边。你们要思念上面的事，不要思念地上的事。"
        ),
        Section(
            id=7,
            en="For ye are dead, and your life is hid with Christ in God. When Christ, who is our life, shall appear, then shall ye also appear with him in glory.",
            cn="因为你们已经死了，你们的生命与基督一同藏在神里面。基督是我们的生命，他显现的时候，你们也要与他一同显现在荣耀里。",
            footnotes=[
                {
                    "marker": "[2]",
                    "content": "这里强调信徒与基督生命的联合",
                    "original": "This emphasizes the believer's union with Christ in life"
                }
            ]
        )
    ]

    chapter3 = Chapter(
        chapter_number=3,
        title="The New Life in Christ",
        title_cn="在基督里的新生命",
        sections=ch3_sections,
        scripture_text="Εἰ οὖν συνηγέρθητε τῷ Χριστῷ, τὰ ἄνω ζητεῖτε",
        scripture_translation="If then you have been raised with Christ, seek the things that are above"
    )

    book = BookContent(
        metadata=metadata,
        preface=[preface_section],
        chapters=[chapter1, chapter2, chapter3]
    )

    return book


def main():
    print("=" * 60)
    print("BOOK DIGITIZATION PIPELINE - DEMO")
    print("=" * 60)
    print("\nThis demo generates sample output without requiring API access.\n")

    # Create sample book
    print("Creating sample book content...")
    book = create_sample_book()

    # Initialize processors
    yaml_processor = YAMLProcessor()
    html_generator = HTMLGenerator()
    latex_generator = LaTeXGenerator()

    # Save to YAML
    print("\n1. Saving to YAML format...")
    yaml_path = yaml_processor.save_book(book, "Colossians_Lightfoot_Demo")

    # Generate HTML
    print("\n2. Generating HTML website...")
    html_path = html_generator.generate_book(book)

    # Generate LaTeX (bilingual version only for demo)
    print("\n3. Generating LaTeX files...")
    tex_path = latex_generator.save_latex(book, OutputMode.BILINGUAL)

    # Summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  YAML:  {yaml_path}")
    print(f"  HTML:  {html_path}")
    print(f"  LaTeX: {tex_path}")

    print(f"\nTo view the HTML website, open:")
    print(f"  {html_path}")

    print(f"\nTo compile the PDF (requires LaTeX installation):")
    print(f"  xelatex {tex_path}")

    print("\nNote: For actual book processing, use the main pipeline:")
    print("  python pipeline.py full <pdf_path> --title 'Book Title' --api-key <your_key>")


if __name__ == "__main__":
    main()
