
import aiohttp
import asyncio
import time
from datetime import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Any
import json
import json
# Install rich for beautiful output: pip install rich aiohttp
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: 'rich' library not installed. Install it with: pip install rich")
    print("Falling back to basic output...\n")

console = Console() if RICH_AVAILABLE else None

class URLShortenerStressTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "test1": {"responses": [], "short_urls": [], "errors": [], "timings": []},
            "test2": {"url1": {"responses": [], "short_urls": [], "errors": [], "timings": []},
                      "url2": {"responses": [], "short_urls": [], "errors": [], "timings": []}},
            "test3": {"responses": [], "status_codes": [], "errors": [], "timings": [], "rate_limited": 0}
        }

    async def make_request(self, session: aiohttp.ClientSession, target_url: str, request_id: int) -> Dict[str, Any]:
        """Make a single POST request to shorten URL"""
        url = f"{self.base_url}/api/shorten?target_url={target_url}"
        headers = {"Content-Type": "application/json"}

        start_time = time.time()
        try:
            async with session.post(url, headers=headers) as response:
                elapsed = time.time() - start_time
                status = response.status

                if status == 201:
                    data = await response.json()
                    return {
                        "request_id": request_id,
                        "status": status,
                        "success": True,
                        "short_url": data.get("short_url", "N/A"),
                        "target_url": target_url,
                        "elapsed": elapsed,
                        "error": None
                    }
                elif status == 429:  # Rate limited
                    text = await response.text()
                    return {
                        "request_id": request_id,
                        "status": status,
                        "success": False,
                        "short_url": None,
                        "target_url": target_url,
                        "elapsed": elapsed,
                        "error": "Rate Limited",
                        "response": text
                    }
                else:
                    text = await response.text()
                    return {
                        "request_id": request_id,
                        "status": status,
                        "success": False,
                        "short_url": None,
                        "target_url": target_url,
                        "elapsed": elapsed,
                        "error": f"HTTP {status}: {text}"
                    }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "request_id": request_id,
                "status": 0,
                "success": False,
                "short_url": None,
                "target_url": target_url,
                "elapsed": elapsed,
                "error": str(e)
            }

    async def test_case_1(self, num_requests: int = 50):
        """Test Case 1: Multiple parallel requests with SAME target URL"""
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Test Case 1:[/bold cyan] Multiple parallel requests with SAME target URL")
            console.print(f"[yellow]Testing {num_requests} concurrent requests...[/yellow]\n")
        else:
            print(f"\nTest Case 1: Multiple parallel requests with SAME target URL")
            print(f"Testing {num_requests} concurrent requests...\n")

        target_url = "https://google.com"

        async with aiohttp.ClientSession() as session:
            tasks = [self.make_request(session, target_url, i) for i in range(num_requests)]
            responses = await asyncio.gather(*tasks)

        # Store results
        for resp in responses:
            self.results["test1"]["responses"].append(resp)
            self.results["test1"]["timings"].append(resp["elapsed"])
            if resp["success"]:
                self.results["test1"]["short_urls"].append(resp["short_url"])
            else:
                self.results["test1"]["errors"].append(resp["error"])

    async def test_case_2(self, num_requests_per_url: int = 25):
        """Test Case 2: Multiple parallel requests with 2 DIFFERENT target URLs"""
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Test Case 2:[/bold cyan] Multiple parallel requests with 2 DIFFERENT target URLs")
            console.print(f"[yellow]Testing {num_requests_per_url} requests for each URL...[/yellow]\n")
        else:
            print(f"\nTest Case 2: Multiple parallel requests with 2 DIFFERENT target URLs")
            print(f"Testing {num_requests_per_url} requests for each URL...\n")

        url1 = "https://google.com"
        url2 = "https://youtube.com"

        async with aiohttp.ClientSession() as session:
            tasks = []
            # Create tasks for both URLs interleaved
            for i in range(num_requests_per_url):
                tasks.append(self.make_request(session, url1, f"url1_{i}"))
                tasks.append(self.make_request(session, url2, f"url2_{i}"))

            responses = await asyncio.gather(*tasks)

        # Store results
        for resp in responses:
            if resp["target_url"] == url1:
                self.results["test2"]["url1"]["responses"].append(resp)
                self.results["test2"]["url1"]["timings"].append(resp["elapsed"])
                if resp["success"]:
                    self.results["test2"]["url1"]["short_urls"].append(resp["short_url"])
                else:
                    self.results["test2"]["url1"]["errors"].append(resp["error"])
            else:
                self.results["test2"]["url2"]["responses"].append(resp)
                self.results["test2"]["url2"]["timings"].append(resp["elapsed"])
                if resp["success"]:
                    self.results["test2"]["url2"]["short_urls"].append(resp["short_url"])
                else:
                    self.results["test2"]["url2"]["errors"].append(resp["error"])

    async def test_case_3(self, requests_under_limit: int = 50, requests_over_limit: int = 20):
        """Test Case 3: Rate limiting test (60 requests per minute)"""
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Test Case 3:[/bold cyan] Rate Limiting Test (60 requests/minute limit)")
            console.print(f"[yellow]Testing {requests_under_limit} requests within limit, then {requests_over_limit} over limit...[/yellow]\n")
        else:
            print(f"\nTest Case 3: Rate Limiting Test (60 requests/minute limit)")
            print(f"Testing {requests_under_limit} requests within limit, then {requests_over_limit} over limit...\n")

        target_url = "https://google.com"

        async with aiohttp.ClientSession() as session:
            # Send initial burst (should mostly succeed if under 60)
            tasks = [self.make_request(session, target_url, i) for i in range(requests_under_limit + requests_over_limit)]
            responses = await asyncio.gather(*tasks)

        # Store results
        for resp in responses:
            self.results["test3"]["responses"].append(resp)
            self.results["test3"]["status_codes"].append(resp["status"])
            self.results["test3"]["timings"].append(resp["elapsed"])
            if resp["status"] == 429:
                self.results["test3"]["rate_limited"] += 1
            if not resp["success"]:
                self.results["test3"]["errors"].append(resp["error"])

    def print_test1_report(self):
        """Print beautiful report for Test Case 1"""
        results = self.results["test1"]
        short_urls = results["short_urls"]
        unique_short_urls = set(short_urls)

        if RICH_AVAILABLE:
            console.print("\n" + "="*80)
            console.print(Panel.fit("[bold green]Test Case 1 Results: Same Target URL[/bold green]",
                                    border_style="green"))

            # Summary table
            table = Table(title="Summary", box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", width=30)
            table.add_column("Value", style="yellow", width=40)

            table.add_row("Total Requests", str(len(results["responses"])))
            table.add_row("Successful Requests", str(len(short_urls)))
            table.add_row("Failed Requests", str(len(results["errors"])))
            table.add_row("Unique Short URLs Generated", str(len(unique_short_urls)))
            table.add_row("✓ Same Short URL for All?",
                          "[green]YES ✓[/green]" if len(unique_short_urls) == 1 else "[red]NO ✗[/red]")

            if short_urls:
                table.add_row("Short URL Generated", short_urls[0] if len(unique_short_urls) == 1 else "MULTIPLE!")
                table.add_row("Avg Response Time", f"{sum(results['timings'])/len(results['timings']):.3f}s")
                table.add_row("Min Response Time", f"{min(results['timings']):.3f}s")
                table.add_row("Max Response Time", f"{max(results['timings']):.3f}s")

            console.print(table)

            # If multiple short URLs detected, show details
            if len(unique_short_urls) > 1:
                console.print("\n[bold red]⚠ WARNING: Multiple short URLs detected for same target![/bold red]")
                url_counts = Counter(short_urls)
                detail_table = Table(title="Short URL Distribution", box=box.SIMPLE)
                detail_table.add_column("Short URL", style="cyan")
                detail_table.add_column("Count", style="yellow")
                for url, count in url_counts.items():
                    detail_table.add_row(url, str(count))
                console.print(detail_table)
        else:
            print("\n" + "="*80)
            print("Test Case 1 Results: Same Target URL")
            print("="*80)
            print(f"Total Requests: {len(results['responses'])}")
            print(f"Successful Requests: {len(short_urls)}")
            print(f"Failed Requests: {len(results['errors'])}")
            print(f"Unique Short URLs Generated: {len(unique_short_urls)}")
            print(f"Same Short URL for All?: {'YES ✓' if len(unique_short_urls) == 1 else 'NO ✗'}")
            if short_urls:
                print(f"Short URL: {short_urls[0] if len(unique_short_urls) == 1 else 'MULTIPLE!'}")
                print(f"Avg Response Time: {sum(results['timings'])/len(results['timings']):.3f}s")

    def print_test2_report(self):
        """Print beautiful report for Test Case 2"""
        url1_results = self.results["test2"]["url1"]
        url2_results = self.results["test2"]["url2"]

        url1_short_urls = set(url1_results["short_urls"])
        url2_short_urls = set(url2_results["short_urls"])
        collision = bool(url1_short_urls & url2_short_urls)  # Check for any overlap

        if RICH_AVAILABLE:
            console.print("\n" + "="*80)
            console.print(Panel.fit("[bold green]Test Case 2 Results: Two Different Target URLs[/bold green]",
                                    border_style="green"))

            table = Table(title="Summary", box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", width=30)
            table.add_column("URL 1", style="yellow", width=20)
            table.add_column("URL 2", style="green", width=20)

            table.add_row("Total Requests",
                          str(len(url1_results["responses"])),
                          str(len(url2_results["responses"])))
            table.add_row("Successful Requests",
                          str(len(url1_results["short_urls"])),
                          str(len(url2_results["short_urls"])))
            table.add_row("Unique Short URLs",
                          str(len(url1_short_urls)),
                          str(len(url2_short_urls)))
            table.add_row("Avg Response Time",
                          f"{sum(url1_results['timings'])/len(url1_results['timings']):.3f}s" if url1_results['timings'] else "N/A",
                          f"{sum(url2_results['timings'])/len(url2_results['timings']):.3f}s" if url2_results['timings'] else "N/A")

            console.print(table)

            # Collision check
            if collision:
                console.print("\n[bold red]⚠ COLLISION DETECTED: Same short URL generated for different targets![/bold red]")
                console.print(f"[red]Colliding URLs: {url1_short_urls & url2_short_urls}[/red]")
            else:
                console.print("\n[bold green]✓ No Collisions: Each target URL has unique short URL(s)[/bold green]")

            # Show actual short URLs
            if url1_short_urls:
                console.print(f"\n[cyan]URL 1 Short URL(s):[/cyan] {', '.join(list(url1_short_urls)[:3])}")
            if url2_short_urls:
                console.print(f"[cyan]URL 2 Short URL(s):[/cyan] {', '.join(list(url2_short_urls)[:3])}")
        else:
            print("\n" + "="*80)
            print("Test Case 2 Results: Two Different Target URLs")
            print("="*80)
            print(f"URL 1 - Requests: {len(url1_results['responses'])}, Unique Short URLs: {len(url1_short_urls)}")
            print(f"URL 2 - Requests: {len(url2_results['responses'])}, Unique Short URLs: {len(url2_short_urls)}")
            print(f"Collision Detected: {'YES ✗' if collision else 'NO ✓'}")

    def print_test3_report(self):
        """Print beautiful report for Test Case 3"""
        results = self.results["test3"]
        status_counter = Counter(results["status_codes"])

        successful = status_counter.get(201, 0)
        rate_limited = status_counter.get(429, 0)

        if RICH_AVAILABLE:
            console.print("\n" + "="*80)
            console.print(Panel.fit("[bold green]Test Case 3 Results: Rate Limiting Test[/bold green]",
                                    border_style="green"))

            table = Table(title="Summary", box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", width=35)
            table.add_column("Value", style="yellow", width=35)

            table.add_row("Total Requests Sent", str(len(results["responses"])))
            table.add_row("Successful (200 OK)", f"[green]{successful}[/green]")
            table.add_row("Rate Limited (429)", f"[red]{rate_limited}[/red]")
            table.add_row("Other Errors", str(len(results["responses"]) - successful - rate_limited))
            table.add_row("✓ Rate Limiting Working?",
                          "[green]YES ✓[/green]" if rate_limited > 0 else "[yellow]MAYBE[/yellow]")

            if results["timings"]:
                table.add_row("Avg Response Time", f"{sum(results['timings'])/len(results['timings']):.3f}s")

            console.print(table)

            # Status code distribution
            if len(status_counter) > 0:
                status_table = Table(title="Status Code Distribution", box=box.SIMPLE)
                status_table.add_column("Status Code", style="cyan")
                status_table.add_column("Count", style="yellow")
                status_table.add_column("Percentage", style="green")

                for status, count in sorted(status_counter.items()):
                    percentage = (count / len(results["responses"])) * 100
                    status_table.add_row(str(status), str(count), f"{percentage:.1f}%")

                console.print(status_table)
        else:
            print("\n" + "="*80)
            print("Test Case 3 Results: Rate Limiting Test")
            print("="*80)
            print(f"Total Requests: {len(results['responses'])}")
            print(f"Successful (200): {successful}")
            print(f"Rate Limited (429): {rate_limited}")
            print(f"Rate Limiting Working?: {'YES ✓' if rate_limited > 0 else 'MAYBE'}")

    async def run_all_tests(self):
        """Run all test cases"""
        start_time = time.time()

        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold blue]URL Shortener Stress Testing Suite[/bold blue]\n" +
                f"[cyan]Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/cyan]",
                border_style="blue"
            ))
        else:
            print("="*80)
            print("URL Shortener Stress Testing Suite")
            print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80)

        # Run tests sequentially
        await self.test_case_1(num_requests=10)
        await asyncio.sleep(2)
        await self.test_case_2(num_requests_per_url=25)
        await asyncio.sleep(2)
        await self.test_case_3(requests_under_limit=50, requests_over_limit=200)

        # Print all reports
        self.print_test1_report()
        self.print_test2_report()
        self.print_test3_report()

        # print(json.dumps(self.results, indent=4))
        # Final summary
        total_time = time.time() - start_time
        if RICH_AVAILABLE:
            console.print("\n" + "="*80)
            console.print(Panel.fit(
                f"[bold green]All Tests Completed![/bold green]\n" +
                f"[cyan]Total Execution Time: {total_time:.2f}s[/cyan]",
                border_style="green"
            ))
        else:
            print("\n" + "="*80)
            print(f"All Tests Completed! Total Time: {total_time:.2f}s")
            print("="*80)

# Main execution
async def main():
    # Configure your server URL here
    BASE_URL = "http://localhost:8080"

    tester = URLShortenerStressTest(BASE_URL)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())