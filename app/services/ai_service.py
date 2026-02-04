
import os
import asyncio
import httpx
from typing import List

class AIService:
    def __init__(self):
        base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3")

        self.api_url = f"{base_url}/api/generate"
        self.model = model
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", 60.0))

        # safety limits
        self.chunk_size = int(os.getenv("OLLAMA_CHUNK_SIZE", 1000))
        self.chunk_overlap = int(os.getenv("OLLAMA_CHUNK_OVERLAP", 100))
        self.max_concurrency = int(os.getenv("OLLAMA_MAX_CONCURRENCY", 2))

    # ---------- 1. Chunking ----------
    def _chunk_text(self, text: str) -> List[str]:
        words = text.split()
        chunks = []

        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunks.append(" ".join(words[start:end]))
            start += self.chunk_size - self.chunk_overlap

        return chunks

    # ---------- 2. Summarize single chunk ----------
    async def _summarize_chunk(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        title: str,
        chunk: str,
        index: int
    ) -> str:
        prompt = (
            f"You are summarizing a section of the book '{title}'.\n\n"
            f"Section content:\n{chunk}\n\n"
            f"Return a concise summary of this section."
        )

        async with semaphore:
            response = await client.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                }
            )

            response.raise_for_status()
            return response.json().get("response", "").strip()

    # ---------- 3. Public API ----------
    async def generate_book_summary(self, title: str, content: str) -> str:
        chunks = self._chunk_text(content)

        semaphore = asyncio.Semaphore(self.max_concurrency)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # MAP phase
            tasks = [
                self._summarize_chunk(client, semaphore, title, chunk, i)
                for i, chunk in enumerate(chunks)
            ]

            partial_summaries = await asyncio.gather(*tasks)

            # REDUCE phase
            combined = "\n".join(partial_summaries)

            final_prompt = (
                f"The following are summaries of sections of the book '{title}':\n\n"
                f"{combined}\n\n"
                f"Create a coherent, concise overall summary of the entire book."
            )

            final_response = await client.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {"temperature": 0.2}
                }
            )

            final_response.raise_for_status()
            return final_response.json().get("response", "").strip()


if __name__ == "__main__":
    async def main():
        ai_service = AIService()
        title = "The Power of Focus"
        content = """ Chapter 1: The Age of Distraction
        In the modern digital world, people are constantly surrounded by notifications, messages, and entertainment. Smartphones, social media platforms, and instant communication tools have reshaped how individuals spend their time and attention. While these technologies have increased convenience, they have also reduced the ability to focus deeply on important tasks.
        Research shows that frequent interruptions can lower productivity and increase mental fatigue. When individuals switch between tasks repeatedly, the brain consumes more energy and becomes less efficient. Over time, this pattern leads to stress, poor decision-making, and reduced creativity.
        Chapter 2: Understanding Focus
        Focus is the ability to concentrate mental energy on a single task without distraction. It is not an inborn talent but a skill that can be developed with practice. Highly successful people are not necessarily more intelligent, but they are better at directing their attention.
        Developing focus requires awareness of one’s habits. Many people underestimate how much time they lose to social media, unnecessary browsing, and multitasking. By tracking daily activities, individuals can identify major sources of distraction.
        Chapter 3: Building Productive Habits
        Creating routines is essential for strengthening focus. When tasks are performed at consistent times and in consistent environments, the brain learns to enter a state of concentration more easily.
        One effective method is time-blocking, where specific hours are dedicated to important work. Another technique is the Pomodoro method, which involves working in focused intervals followed by short breaks. These strategies help maintain motivation and reduce burnout.
        Chapter 4: The Role of Environment
        A cluttered environment can negatively affect mental clarity. Noise, poor lighting, and uncomfortable seating can reduce concentration. Designing a workspace that is quiet, well-lit, and organized improves performance.
        Digital environments also matter. Disabling unnecessary notifications, organizing files, and using focus tools can significantly enhance productivity.
        Chapter 5: Long-Term Mastery
        Mastering focus is a lifelong process. It requires consistent effort, reflection, and adjustment. As responsibilities change, individuals must adapt their strategies.
        Those who cultivate deep focus gain a competitive advantage in their careers and personal lives. They are able to learn faster, solve complex problems, and produce higher-quality work.
        In conclusion, focus is not merely about avoiding distractions. It is about intentionally directing one’s energy toward meaningful goals. By developing strong habits, managing the environment, and practicing self-discipline, anyone can improve their ability to concentrate and achieve long-term success.
        """
        summary = await ai_service.generate_book_summary(title, content)
        print("Final Summary:")
        print(summary)

    asyncio.run(main())