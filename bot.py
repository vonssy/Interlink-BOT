from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from base64 import urlsafe_b64decode
from datetime import datetime
from colorama import *
import asyncio, random, time, json, sys, re, os

class Interlink:
    def __init__(self) -> None:
        self.BASE_API = "https://prod.interlinklabs.ai"
        self.VERSION = "5.0.0"

        self.USE_PROXY = False
        self.ROTATE_PROXY = False

        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Interlink Labs {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
        
    def save_accounts(self, new_accounts):
        filename = "accounts.json"
        try:
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                with open(filename, 'r') as file:
                    existing_accounts = json.load(file)
            else:
                existing_accounts = []

            account_dict = {acc["email"]: acc for acc in existing_accounts}

            for new_acc in new_accounts:
                email = new_acc["email"]

                if email in account_dict:
                    account_dict[email].update(new_acc)
                else:
                    account_dict[email] = new_acc

            updated_accounts = list(account_dict.values())

            with open(filename, 'w') as file:
                json.dump(updated_accounts, file, indent=4)

        except Exception as e:
            return []
    
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def display_proxy(self, proxy_url=None):
        if not proxy_url: return "No Proxy"

        proxy_url = re.sub(r"^(http|https|socks4|socks5)://", "", proxy_url)

        if "@" in proxy_url:
            proxy_url = proxy_url.split("@", 1)[1]

        return proxy_url
    
    def decode_token(self, email: str):
        try:
            access_token = self.accounts[email]["accessToken"]
            header, payload, signature = access_token.split(".")
            decoded_payload = urlsafe_b64decode(payload + "==").decode("utf-8")
            parsed_payload = json.loads(decoded_payload)
            exp_time = parsed_payload["exp"]
            
            return exp_time
        except Exception as e:
            return None
    
    def mask_account(self, account):
        if "@" in account:
            local, domain = account.split('@', 1)
            mask_account = local[:3] + '*' * 3 + local[-3:]
            return f"{mask_account}@{domain}"
        
    def generate_device_id(self):
        return str(os.urandom(8).hex())
    
    def generate_timestamp(self):
        return str(int(time.time()) * 1000)
        
    def initialize_headers(self, email: str):
        headers = {
            "Host": "prod.interlinklabs.ai",
            "Accept": "*/*",
            "Version": self.VERSION,
            "X-Platform": "android",
            "X-Date": self.generate_timestamp(),
            "X-Unique-Id": self.accounts[email]["deviceId"],
            "X-Model": "25053PC47G",
            "X-Brand": "POCO",
            "X-System-Name": "Android",
            "X-Device-Id": self.accounts[email]["deviceId"],
            "X-Bundle-Id": "org.ai.interlinklabs.interlinkId",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "okhttp/4.12.0"
        }

        return headers.copy()

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    self.USE_PROXY = True if proxy_choice == 1 else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1  or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1  or 2).{Style.RESET_ALL}")

        if self.USE_PROXY:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()
                if rotate_proxy in ["y", "n"]:
                    self.ROTATE_PROXY = True if rotate_proxy == "y" else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

    async def enusre_ok(self, response):
        if response.status >= 400:
            raise Exception(f"HTTP: {response.status}:{await response.text()}")

    async def check_connection(self, email: str, proxy_url=None):
        url = "https://api.ipify.org?format=json"
        
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=15)) as session:
                async with session.get(url=url, proxy=proxy, proxy_auth=proxy_auth) as response:
                    await self.enusre_ok(response)
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
    
    async def refresh_token(self, email: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/auth/token"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(email)
                headers["Authorization"] = f"Bearer {self.accounts[email]['accessToken']}"
                headers["Content-Type"] = "application/json"
                payload = {
                    "refreshToken": self.accounts[email]["refreshToken"]
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.enusre_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Refreshing Tokens {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def user_info(self, email: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/auth/current-user-full"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(email)
                headers["Authorization"] = f"Bearer {self.accounts[email]['accessToken']}"

                params = {
                    "include": "userInfo,token,isClaimable"
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.enusre_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}User   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Info {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
            
    async def claim_airdrop(self, email: str, proxy_url=None, retries=1):
        url = f"{self.BASE_API}/api/v1/token/claim-airdrop"

        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(email)
                headers["Authorization"] = f"Bearer {self.accounts[email]['accessToken']}"
                headers["Content-Type"] = "application/json"

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json={}, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.enusre_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Mining :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
            
    async def group_mining_list(self, email: str, proxy_url=None, retries=1):
        url = f"{self.BASE_API}/api/v1/group-mining/get-list-group-mining"

        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(email)
                headers["Authorization"] = f"Bearer {self.accounts[email]['accessToken']}"
                headers["Content-Type"] = "application/json"

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json={}, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.enusre_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Group  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch List {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
            
    async def claim_group_mining(self, email: str, group_id: str, proxy_url=None, retries=1):
        url = f"{self.BASE_API}/api/v1/group-mining/claim-group-mining"

        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(email)
                headers["Authorization"] = f"Bearer {self.accounts[email]['accessToken']}"
                headers["Content-Type"] = "application/json"

                payload = {
                    "groupId": group_id
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.enusre_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}Group{Style.RESET_ALL}"
                    f"{Fore.BLUE+Style.BRIGHT} {group_id} {Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT}Failed to Claim{Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT}{str(e)}{Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, email: str, proxy_url=None):
        while True:
            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(email)

            is_valid = await self.check_connection(proxy_url)
            if is_valid: return True
            
            if self.ROTATE_PROXY:
                proxy_url = self.rotate_proxy_for_account(email)
                await asyncio.sleep(1)
                continue

            return False
            
    async def process_check_tokens(self, email: str, proxy_url=None):
        exp_time = self.decode_token(email)
        if not exp_time:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Invalid Token {Style.RESET_ALL}"
            )
            return False

        if int(time.time()) > exp_time:
            refresh = await self.refresh_token(email, proxy_url)
            if not refresh: return False

            self.accounts[email]["accessToken"] = refresh.get("data", {}).get("accessToken")
            self.accounts[email]["refreshToken"] = refresh.get("data", {}).get("refreshToken")

            account_data = [{
                "email": email,
                "interlinkId": self.accounts[email]["interlinkId"],
                "passcode": self.accounts[email]["passcode"],
                "deviceId": self.accounts[email]["deviceId"],
                "tokens": {
                    "accessToken": self.accounts[email]["accessToken"],
                    "refreshToken": self.accounts[email]["refreshToken"]
                }
            }]
            self.save_accounts(account_data)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Tokens Refreshed {Style.RESET_ALL}"
            )

        return True

    async def process_accounts(self, email: str, proxy_url=None):
        is_ok = await self.process_check_connection(email, proxy_url)
        if not is_ok: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(email)

        is_valid = await self.process_check_tokens(email, proxy_url)
        if not is_valid: return False

        user = await self.user_info(email, proxy_url)
        if user:
            balance = user.get("data", {}).get("token", {}).get("interlinkGoldTokenAmount", 0)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Balance:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} $ITLG {Style.RESET_ALL}"
            )

            is_claimable = user.get("data", {}).get("isClaimable", {}).get("isClaimable", False)
            if is_claimable:
                claim = await self.claim_airdrop(email, proxy_url)
                if claim:
                    reward = claim.get("data") or "N/A"

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Mining :{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} Claimed Successfully {Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{reward}{Style.RESET_ALL}"
                    )
            
            else:
                next_frame_ts = user.get("data", {}).get("isClaimable", {}).get("nextFrame", 0)
                formatted_next_frame = datetime.fromtimestamp(next_frame_ts / 1000).strftime('%x %X')

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Mining :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.CYAN+Style.BRIGHT} Next Claim at: {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{formatted_next_frame}{Style.RESET_ALL}"
                )

        group_list = await self.group_mining_list(email, proxy_url)
        if group_list:
            next_claimable = group_list.get("data", {}).get("nextTimeClaim", 0)
            groups = group_list.get("data", {}).get("groups", [])

            if groups != []:
                self.log(f"{Fore.CYAN+Style.BRIGHT}Group  :{Style.RESET_ALL}")

                for group in groups:
                    group_id = group.get("groupId")
                    reward = group.get("totalReward")
                    secure = group.get("secure")
                    can_claim = group.get("canClaim")

                    if not secure:
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}Group{Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT} {group_id} {Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT}Not Secured{Style.RESET_ALL}"
                        )
                        continue

                    if not can_claim:
                        formatted_next_frame = datetime.fromtimestamp(next_claimable / 1000).strftime('%x %X')
                        self.log(
                            f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}Group{Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT} {group_id} {Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT}Already Claimed{Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT}Next Claim at:{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {formatted_next_frame} {Style.RESET_ALL}"
                        )
                        continue

                    claim = await self.claim_group_mining(email, group_id, proxy_url)
                    if not claim: continue

                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT} ● {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}Group{Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT} {group_id} {Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT}Claimed{Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}Reward:{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {reward} $ITLG {Style.RESET_ALL}"
                    )

            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Group  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} No Available Mining Group {Style.RESET_ALL}"
                )
        
    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(f"{Fore.RED}No Accounts Loaded.{Style.RESET_ALL}")
                return

            self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if self.USE_PROXY: self.load_proxies()
        
                separator = "=" * 28
                for idx, account in enumerate(accounts, start=1):
                    email = account.get("email")
                    interlink_id = account.get("interlinkId")
                    passcode = account.get("passcode")
                    device_id = account.get("deviceId")
                    tokens = account.get("tokens", {})
                    access_token = tokens.get("accessToken")
                    refresh_token = tokens.get("refreshToken")

                    if device_id is None:
                        device_id = self.generate_device_id()

                    account_data = [{
                        "email": email,
                        "interlinkId": interlink_id,
                        "passcode": passcode,
                        "deviceId": device_id,
                        "tokens": {
                            "accessToken": access_token,
                            "refreshToken": refresh_token
                        }
                    }]
                    self.save_accounts(account_data)

                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}Of{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {len(accounts)} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                    )

                    if "@" not in email or not interlink_id or not passcode or not device_id or not access_token or not refresh_token:
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Status :{Style.RESET_ALL}"
                            f"{Fore.RED+Style.BRIGHT} Invalid Account Data {Style.RESET_ALL}"
                        )
                        continue

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Account:{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(email)} {Style.RESET_ALL}"
                    )

                    self.accounts[email] = {
                        "interlinkId": interlink_id,
                        "passcode": passcode,
                        "deviceId": device_id,
                        "accessToken": access_token,
                        "refreshToken": refresh_token
                    }
                    
                    await self.process_accounts(email)
                    await asyncio.sleep(random.uniform(2.0, 3.0))

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*67)
                seconds = 4 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Interlink()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Interlink - BOT{Style.RESET_ALL}                                       "                              
        )
        sys.exit(1)