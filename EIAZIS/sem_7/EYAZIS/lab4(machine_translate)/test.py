import time
import statistics
import textwrap
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.tokenize import word_tokenize
from difflib import SequenceMatcher
from deep_translator import GoogleTranslator
from translation_engine import AdvancedTranslator

# Color codes for terminal output
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

# ==========================================
# LONG TEST DATA
# ==========================================

CS_TEXTS = [
    # 1. Machine Learning / Neural Networks
    "Deep learning architectures, specifically convolutional neural networks (CNNs), have revolutionized the field of computer vision by automatically learning hierarchical feature representations from raw data. Unlike traditional algorithms where features are hand-engineered, CNNs utilize backpropagation to adjust weights across multiple hidden layers, allowing the system to minimize the loss function and improve classification accuracy over epochs.",

    # 2. Database Systems (ACID)
    "In the context of relational database management systems, ACID properties—Atomicity, Consistency, Isolation, and Durability—guarantee that database transactions are processed reliably. Atomicity ensures that a transaction is treated as a single unit, which either completely succeeds or completely fails, preventing data corruption resulting from partial execution during power failures or system crashes.",

    # 3. Cybersecurity (Public Key Infrastructure)
    "Public Key Infrastructure (PKI) serves as the foundation for secure internet communication by managing digital certificates and public-key encryption. When a user connects to a secure server via HTTPS, the server presents a certificate signed by a trusted Certificate Authority (CA), verifying the server's identity and enabling the exchange of a symmetric session key for encrypted data transfer.",

    # 4. Software Engineering (Microservices)
    "The shift from monolithic architectures to microservices has allowed organizations to scale applications by decomposing them into loosely coupled, independently deployable services. While this approach improves agility and fault isolation, it introduces significant complexity regarding inter-service communication, data consistency, and distributed tracing, often requiring an orchestration layer like Kubernetes.",

    # 5. Operating Systems (Memory Management)
    "Virtual memory is a memory management technique that creates an illusion for users of a very large (main) memory. It maps memory addresses used by a program, called virtual addresses, into physical addresses in computer memory. This allows the execution of processes that may not be completely in the main memory, effectively separating the logical memory as perceived by users from physical memory."
]

LIT_TEXTS = [
    # 1. Atmospheric / Gothic
    "The fog rolled in from the harbor like a thick, gray blanket, swallowing the gas lamps one by one until the cobblestone streets were reduced to a hazy memory. Silence hung heavy in the air, broken only by the distant, mournful toll of the cathedral bell, which seemed to count down the minutes to an inevitable and unseen calamity that the city slept through unknowingly.",

    # 2. Character Introspection
    "He stood before the mirror, tracing the lines that time had etched into his face, wondering when exactly the boy he remembered had vanished to make room for this weary stranger. It was not a sudden change, but a slow erosion of spirit, chipped away by compromised dreams and the relentless, grinding friction of daily compromise until only the hollow shell of his ambition remained.",

    # 3. Nature / Romanticism
    "The valley stretched out beneath us in a riot of autumn colors, a patchwork quilt of burning crimsons and melancholy golds stitched together by the silver thread of the winding river. The wind whispered through the ancient pines, carrying the scent of damp earth and decaying leaves, a reminder that in nature, death is not an end, but merely the fertile soil for the next season's rebirth.",

    # 4. Abstract / Stream of Consciousness
    "Time did not move in a straight line here; it pooled in the corners of the room, stagnant and thick, trapping moments like insects in amber. She felt the past and the present overlapping, a double exposure on the film of her mind, where the laughter of children long grown echoed against the silence of the empty hallway, blurring the distinction between what was real and what was merely remembered.",

    # 5. Social Commentary
    "The industrial city was a machine that consumed its own creators, a sprawling beast of iron and steam that belched smoke into a sky that had forgotten the color blue. Below, the workers moved with the rhythmic precision of pistons, their individual identities submerged beneath the collective necessity of production, trading their days for a pittance in a world that valued efficiency over humanity."
]


class TranslationTestSuite:
    def __init__(self):
        print(f"{BOLD}Initializing Translation Engine...{RESET}")
        # Disable cache to force fresh generation
        self.engine = AdvancedTranslator(use_cache=False)
        self.back_translator = GoogleTranslator(source='de', target='en')
        self.smoother = SmoothingFunction().method1

    def calculate_similarity(self, original, back_translated):
        """
        Calculates similarity using SequenceMatcher and BLEU.
        Note: For long texts, exact sequence matching is naturally lower.
        """
        # 1. Sequence Matcher
        seq_similarity = SequenceMatcher(None, original, back_translated).ratio() * 100

        # 2. BLEU Score
        ref = [word_tokenize(original.lower())]
        cand = word_tokenize(back_translated.lower())
        try:
            # Method 1 is better for sentence-level, Method 4 usually better for corpus
            # We use method1 here as a general smoother for short paragraphs
            bleu = sentence_bleu(ref, cand, smoothing_function=self.smoother)
        except:
            bleu = 0

        return seq_similarity, bleu

    def wrap_text(self, text, width=80, indent="  "):
        """Helper to format long text blocks for terminal"""
        wrapper = textwrap.TextWrapper(width=width, initial_indent=indent, subsequent_indent=indent)
        return wrapper.fill(text)

    def run_single_test(self, category, index, text):
        print(f"\n{'-' * 80}")
        print(f"{BOLD}Test {category} #{index + 1}:{RESET}")
        print(f"{BOLD}Original:{RESET}")
        print(self.wrap_text(text))

        # Step 1: Translate to German
        start_time = time.time()
        result = self.engine.translate_with_stats(text)
        duration = time.time() - start_time
        german_text = result.get('translation', '')

        if result.get('error'):
            print(f"{RED}Translation Failed:{RESET} {german_text}")
            return None

        print(f"\n{BOLD}German (Local Engine) [{duration:.2f}s]:{RESET}")
        print(f"{CYAN}{self.wrap_text(german_text)}{RESET}")

        # Step 2: Back Translate
        try:
            # GoogleTranslator has a limit (usually 5000 chars), our texts are safe (~500 chars)
            back_translated = self.back_translator.translate(german_text)
            print(f"\n{BOLD}Back-Translation (Google):{RESET}")
            print(f"{YELLOW}{self.wrap_text(back_translated)}{RESET}")
        except Exception as e:
            print(f"{RED}Back-translation connection failed:{RESET} {e}")
            return None

        # Step 3: Compare
        seq_score, bleu_score = self.calculate_similarity(text, back_translated)

        print(f"\n{BOLD}Metrics:{RESET}")
        print(f"  • Semantic Similarity: {GREEN}{seq_score:.2f}%{RESET}")
        print(f"  • BLEU Score:          {GREEN}{bleu_score:.4f}{RESET}")

        return {
            'category': category,
            'similarity': seq_score,
            'bleu': bleu_score
        }

    def run(self):
        results = []

        print(f"\n{BOLD}=== STARTING LONG-TEXT TRANSLATION TEST SUITE ==={RESET}")
        print("Model: " + self.engine.model_name)
        print("Note: With long texts, exact wording matches are rare. Focus on meaning retention.")

        # Test CS Texts
        for i, text in enumerate(CS_TEXTS):
            res = self.run_single_test("CS", i, text)
            if res: results.append(res)

        # Test Literature Texts
        for i, text in enumerate(LIT_TEXTS):
            res = self.run_single_test("LIT", i, text)
            if res: results.append(res)

        self.print_summary(results)

    def print_summary(self, results):
        if not results:
            print("No results generated.")
            return

        cs_scores = [r['similarity'] for r in results if r['category'] == 'CS']
        lit_scores = [r['similarity'] for r in results if r['category'] == 'LIT']

        cs_bleu = [r['bleu'] for r in results if r['category'] == 'CS']
        lit_bleu = [r['bleu'] for r in results if r['category'] == 'LIT']

        avg_cs = statistics.mean(cs_scores) if cs_scores else 0
        avg_lit = statistics.mean(lit_scores) if lit_scores else 0

        print(f"\n{BOLD}{'=' * 30} SUMMARY REPORT {'=' * 30}{RESET}")
        print(f"{'Category':<15} | {'Avg Similarity':<15} | {'Avg BLEU Score':<15}")
        print("-" * 55)
        print(f"{'Computer Sci':<15} | {avg_cs:>14.2f}% | {statistics.mean(cs_bleu):>14.4f}")
        print(f"{'Literature':<15} | {avg_lit:>14.2f}% | {statistics.mean(lit_bleu):>14.4f}")
        print("-" * 55)

        print(f"\n{BOLD}Analysis:{RESET}")
        print("Interpreting scores for long texts:")
        print("  • Similarity > 40%: Good semantic retention.")
        print("  • BLEU > 0.3:       Excellent machine translation quality.")
        print("  • BLEU < 0.15:      Potential loss of context or drift.")

        if avg_cs > avg_lit:
            print(f"\n{GREEN}Conclusion: The model handled technical jargon better than literary style.{RESET}")
        else:
            print(f"\n{GREEN}Conclusion: The model handled literary flow better than technical jargon.{RESET}")


if __name__ == "__main__":
    tester = TranslationTestSuite()
    tester.run()