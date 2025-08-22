"""
Discord notification module for sending contract addresses.
"""

import logging
import time
from typing import Optional
from discord_webhook import DiscordWebhook, DiscordEmbed
from config import Config

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Handles Discord webhook notifications for coin matches."""
    
    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL
        self.last_send_time = 0
        
    def _rate_limit(self) -> None:
        """Implement rate limiting for Discord webhooks."""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        min_interval = 1.0  # Minimum 1 second between Discord messages
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_send_time = time.time()
        
    def send_enhanced_token_notification_with_buttons(self, token_data: dict, matched_keyword: str = None, discord_bot=None) -> bool:
        """
        Send enhanced token notification with market data, links, and quick buy buttons.
        
        Args:
            token_data: Dictionary containing token information and market data
            matched_keyword: The keyword that matched this token
            discord_bot: Discord bot instance for sending with buttons
            
        Returns:
            True if successful, False otherwise
        """
        # Import Discord components for buttons
        try:
            import discord
            from quick_buy_buttons import QuickBuyView
        except ImportError:
            logger.warning("Discord or QuickBuyView not available, sending webhook notification")
            return self.send_enhanced_token_notification(token_data, matched_keyword)
        
        # EMERGENCY NUCLEAR BLOCK: Validate token age before ANY notification
        token_address = token_data.get('address', '')
        blocked_tokens = [
            "EK7Ko9zmrfanDz98UnbWB9zkDPFV3Mcpx84t1DS2bonk",
            "7Zje1wV3r5sq8JEvJ1jFWifmSZe6CSBLRz4prFSXbonk", 
            "AHX7mj5Re2AwfvDgQUdVqEidQKHfH4tuxhdaLyLnbonk",
            "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",
            "4EPMN1CVGmWmxF4bBP4Nt4TjD2m5KTjWGMDDrt38bonk",
            "3ZWWatVxckSWHm1avfC5UFyHa4nN9x46KfhWq4Tqbonk"
        ]
        
        if token_address in blocked_tokens:
            logger.error(f"🚨🚨🚨 DISCORD NOTIFIER EMERGENCY BLOCK: {token_address} is BLOCKED")
            logger.error(f"   🚫 Token: {token_data.get('name', 'unknown')} - USER COMPLAINED ABOUT THIS TOKEN")
            return False
        # ACCURATE AGE CALCULATION in Discord Notifier
        import time
        created_timestamp = token_data.get('created_timestamp')
        accurate_age_display = None
        
        if created_timestamp and created_timestamp > 0:
            current_time = time.time()
            if created_timestamp > 1e12:  # Handle milliseconds
                normalized_timestamp = created_timestamp / 1000.0
            else:
                normalized_timestamp = created_timestamp
            
            age_seconds = current_time - normalized_timestamp
            
            # Calculate accurate age display
            if age_seconds < 60:
                accurate_age_display = f"{age_seconds:.0f}s ago"
            elif age_seconds < 3600:
                accurate_age_display = f"{age_seconds/60:.0f}m {age_seconds%60:.0f}s ago"
            else:
                accurate_age_display = f"{age_seconds/3600:.0f}h {(age_seconds%3600)/60:.0f}m ago"
        
        # If no Discord bot available, fall back to webhook
        if not discord_bot:
            logger.info("No Discord bot available, sending webhook notification")
            return self.send_enhanced_token_notification(token_data, matched_keyword)
            
        try:
            self._rate_limit()
            
            # Extract token info
            name = token_data.get('name', f'Token {token_data.get("address", "")[-6:]}')
            symbol = token_data.get('symbol', 'UNK')
            address = token_data.get('address', '')
            # Use accurate age display if calculated, otherwise fallback to token_data  
            age_display = accurate_age_display if accurate_age_display else token_data.get('age_display', 'Unknown')
            market_data = token_data.get('market_data', {})
            
            # Create rich embed with enhanced formatting - MOBILE COPY OPTIMIZED
            embed = discord.Embed(
                title=f"🚨 NEW TOKEN DETECTED",
                description=f"**{name}** ({symbol})\n\n`{address}`",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            
            # Token Info Field with Full Contract Address
            token_info = f"**Name:** {name}\n**Symbol:** {symbol}\n**Age:** {age_display}"
            embed.add_field(
                name="📊 Token Info",
                value=token_info,
                inline=True
            )
            

            
            # Market Data Field - Fetch real-time data from DexScreener
            market_value = ""
            try:
                # Always try to fetch fresh market data from DexScreener API
                import requests
                import json
                
                # Fetch from DexScreener API directly
                try:
                    dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
                    response = requests.get(dex_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get('pairs', [])
                        if pairs:
                            # Get the pair with highest liquidity
                            best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
                            market_data = {
                                'price': float(best_pair.get('priceUsd', 0)),
                                'market_cap': float(best_pair.get('marketCap', 0)),
                                'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                                'liquidity': float(best_pair.get('liquidity', {}).get('usd', 0))
                            }
                            logger.info(f"Fetched market data from DexScreener for {address}")
                except Exception as e:
                    logger.warning(f"DexScreener API failed for {address}: {e}")
                
                # Format market data with MARKET CAP prominently displayed first
                if market_data:
                    # ALWAYS show market cap first - most important metric
                    if market_data.get('market_cap') and market_data['market_cap'] > 0:
                        mc = market_data['market_cap']
                        if mc >= 1_000_000:
                            market_value += f"💰 **MARKET CAP: ${mc/1_000_000:.2f}M**\n"
                        elif mc >= 1_000:
                            market_value += f"💰 **MARKET CAP: ${mc/1_000:.1f}K**\n"
                        else:
                            market_value += f"💰 **MARKET CAP: ${mc:.2f}**\n"
                    else:
                        market_value += f"💰 **MARKET CAP:** Loading...\n"
                    
                    if market_data.get('price'):
                        market_value += f"💵 **Price:** ${market_data['price']:.8f}\n"
                    if market_data.get('volume_24h'):
                        vol = market_data['volume_24h']
                        if vol >= 1_000_000:
                            market_value += f"📊 **24h Volume:** ${vol/1_000_000:.1f}M"
                        elif vol >= 1_000:
                            market_value += f"📊 **24h Volume:** ${vol/1_000:.0f}K"
                        else:
                            market_value += f"📊 **24h Volume:** ${vol:,.0f}"
                
                # Always show market data field with market cap prominently displayed
                embed.add_field(
                    name="💰 Live Market Data",
                    value=market_value or "💰 **MARKET CAP:** Fetching...\n💵 **Price:** Loading...\n📊 **Volume:** Check DexScreener",
                    inline=True
                )
            except Exception as e:
                # Show error instead of loading
                embed.add_field(
                    name="💰 Market Data",
                    value="**Market Cap:** Check DexScreener link\n**Price:** Refreshing...",
                    inline=True
                )
            
            # Platform Info Field
            embed.add_field(
                name="🚀 Platform",
                value="**Source:** PumpFun\n**Network:** Solana",
                inline=True
            )
            
            # Links Field
            links_text = f"[PumpFun](https://pump.fun/{address})\n"
            links_text += f"[DexScreener](https://dexscreener.com/solana/{address})\n"
            links_text += f"[SolScan](https://solscan.io/token/{address})"
            
            embed.add_field(
                name="🔗 Trading Links",
                value=links_text,
                inline=False
            )
            
            # Add extracted social media links if available
            social_links = token_data.get('social_links', [])
            if social_links:
                social_text = ""
                for link in social_links[:5]:  # Limit to 5 links to avoid spam
                    if "x.com" in link or "twitter.com" in link:
                        social_text += f"[Twitter/X]({link})\n"
                    elif "tiktok.com" in link:
                        social_text += f"[TikTok]({link})\n"
                    elif "t.me" in link:
                        social_text += f"[Telegram]({link})\n"
                    elif "discord" in link:
                        social_text += f"[Discord]({link})\n"
                    elif "instagram.com" in link:
                        social_text += f"[Instagram]({link})\n"
                    elif "youtube.com" in link:
                        social_text += f"[YouTube]({link})\n"
                    else:
                        # Generic social link
                        domain = link.split("//")[-1].split("/")[0]
                        social_text += f"[{domain}]({link})\n"
                
                if social_text:
                    embed.add_field(
                        name="📱 Social Media Links",
                        value=social_text.strip(),
                        inline=False
                    )
            
            if matched_keyword:
                embed.add_field(
                    name="🎯 Matched Keyword",
                    value=f"`{matched_keyword}`",
                    inline=True
                )
            
            embed.set_footer(text="⚡ Click buttons below to buy instantly • $0/month monitoring cost")
            
            # Create quick buy buttons view
            view = QuickBuyView(address, name)
            
            # Send message with interactive quick buy buttons through Discord bot
            import os
            import asyncio
            channel_id = os.getenv('DISCORD_CHANNEL_ID')
            
            # Use the Discord bot to send message with interactive buttons
            try:
                # Create asyncio task to send message with buttons
                async def send_notification_with_buttons():
                    try:
                        if channel_id:
                            channel = discord_bot.get_channel(int(channel_id))
                        else:
                            # Use the first available channel from the bot
                            channel = next(iter(discord_bot.get_all_channels()), None)
                        
                        if channel and hasattr(channel, 'send'):
                            # Send message with interactive quick buy buttons
                            message = await channel.send(embed=embed, view=view)
                            logger.info(f"📱 Sent Discord notification with quick buy buttons for {name}")
                            return True
                        else:
                            logger.error(f"Could not find valid Discord channel")
                            return False
                    except Exception as e:
                        logger.error(f"Error sending Discord message with buttons: {e}")
                        return False
                
                # Schedule the async task
                if discord_bot.loop and discord_bot.loop.is_running():
                    # If bot loop is running, create a task
                    future = asyncio.run_coroutine_threadsafe(send_notification_with_buttons(), discord_bot.loop)
                    success = future.result(timeout=5.0)
                else:
                    # Fallback method
                    success = asyncio.run(send_notification_with_buttons())
                
                if success:
                    return True
                    
            except Exception as e:
                logger.error(f"Error with Discord bot notification: {e}")
            
            # Fallback to webhook if Discord bot fails
            logger.info("Falling back to webhook notification")
            return self.send_enhanced_token_notification(token_data, matched_keyword)
            
        except Exception as e:
            logger.error(f"Error sending Discord notification with buttons: {e}")
            # Fallback to webhook notification
            return self.send_enhanced_token_notification(token_data, matched_keyword)
    
    def send_enhanced_token_notification(self, token_data: dict, matched_keyword: str = None) -> bool:
        """
        Send enhanced token notification with market data and links.
        
        Args:
            token_data: Dictionary containing token information and market data
            
        Returns:
            True if successful, False otherwise
        """
        # EMERGENCY NUCLEAR BLOCK: Validate token age before ANY notification
        token_address = token_data.get('address', '')
        blocked_tokens = [
            "EK7Ko9zmrfanDz98UnbWB9zkDPFV3Mcpx84t1DS2bonk",
            "7Zje1wV3r5sq8JEvJ1jFWifmSZe6CSBLRz4prFSXbonk", 
            "AHX7mj5Re2AwfvDgQUdVqEidQKHfH4tuxhdaLyLnbonk",
            "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",
            "4EPMN1CVGmWmxF4bBP4Nt4TjD2m5KTjWGMDDrt38bonk",
            "3ZWWatVxckSWHm1avfC5UFyHa4nN9x46KfhWq4Tqbonk"
        ]
        
        if token_address in blocked_tokens:
            logger.error(f"🚨🚨🚨 DISCORD NOTIFIER EMERGENCY BLOCK: {token_address} is BLOCKED")
            logger.error(f"   🚫 Token: {token_data.get('name', 'unknown')} - USER COMPLAINED ABOUT THIS TOKEN")
            return False
        # ACCURATE AGE CALCULATION in Discord Notifier (Webhook)
        import time
        created_timestamp = token_data.get('created_timestamp')
        accurate_age_display = None
        
        if created_timestamp and created_timestamp > 0:
            current_time = time.time()
            if created_timestamp > 1e12:  # Handle milliseconds
                normalized_timestamp = created_timestamp / 1000.0
            else:
                normalized_timestamp = created_timestamp
            
            age_seconds = current_time - normalized_timestamp
            
            # Calculate accurate age display
            if age_seconds < 60:
                accurate_age_display = f"{age_seconds:.0f}s ago"
            elif age_seconds < 3600:
                accurate_age_display = f"{age_seconds/60:.0f}m {age_seconds%60:.0f}s ago"
            else:
                accurate_age_display = f"{age_seconds/3600:.0f}h {(age_seconds%3600)/60:.0f}m ago"
        
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
            
        try:
            self._rate_limit()
            
            # Create webhook and embed
            webhook = DiscordWebhook(url=self.webhook_url)
            
            # Extract token info
            name = token_data.get('name', f'Token {token_data.get("address", "")[-6:]}')
            symbol = token_data.get('symbol', 'UNK')
            address = token_data.get('address', '')
            # Use accurate age display if calculated, otherwise fallback to token_data
            age_display = accurate_age_display if accurate_age_display else token_data.get('age_display', 'Unknown')
            market_data = token_data.get('market_data', {})
            
            # Create rich embed
            embed = DiscordEmbed(
                title=f"🎯 {name}",
                description=f"**{symbol}** - New Token Match",
                color=0x00ff00
            )
            
            # Token Info Field
            token_info = f"**Symbol:** {symbol}\n**Age:** {age_display}"
            embed.add_embed_field(
                name="📊 Token Info",
                value=token_info,
                inline=True
            )
            
            # Market Data Field - Fetch real-time data from DexScreener
            market_value = ""
            try:
                # Always try to fetch fresh market data from DexScreener API
                import requests
                
                # Fetch from DexScreener API directly
                try:
                    dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
                    response = requests.get(dex_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        pairs = data.get('pairs', [])
                        if pairs:
                            # Get the pair with highest liquidity
                            best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
                            market_data = {
                                'price': float(best_pair.get('priceUsd', 0)),
                                'market_cap': float(best_pair.get('marketCap', 0)),
                                'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                                'liquidity': float(best_pair.get('liquidity', {}).get('usd', 0))
                            }
                            logger.info(f"Fetched market data from DexScreener for {address}")
                except Exception as e:
                    logger.warning(f"DexScreener API failed for {address}: {e}")
                
                # Format market data for display
                if market_data:
                    if market_data.get('market_cap'):
                        mc = market_data['market_cap']
                        if mc >= 1_000_000:
                            market_value += f"**Market Cap:** ${mc/1_000_000:.1f}M\n"
                        elif mc >= 1_000:
                            market_value += f"**Market Cap:** ${mc/1_000:.0f}K\n"
                        else:
                            market_value += f"**Market Cap:** ${mc:.0f}\n"
                    
                    if market_data.get('price'):
                        market_value += f"**Price:** ${market_data['price']:.8f}\n"
                    if market_data.get('volume_24h'):
                        vol = market_data['volume_24h']
                        if vol >= 1_000_000:
                            market_value += f"**24h Volume:** ${vol/1_000_000:.1f}M"
                        elif vol >= 1_000:
                            market_value += f"**24h Volume:** ${vol/1_000:.0f}K"
                        else:
                            market_value += f"**24h Volume:** ${vol:.0f}"
                
                if market_value:
                    embed.add_embed_field(
                        name="💰 Market Data",
                        value=market_value,
                        inline=True
                    )
                else:
                    # Show "Not yet available" instead of "Loading..."
                    embed.add_embed_field(
                        name="💰 Market Data",
                        value="**Market Cap:** Not yet available\n**Price:** Check DexScreener link\n**24h Volume:** Not yet available",
                        inline=True
                    )
            except Exception as e:
                # Show error instead of loading
                embed.add_embed_field(
                    name="💰 Market Data",
                    value="**Market Cap:** Check DexScreener link\n**Price:** Refreshing...",
                    inline=True
                )
            
            # Links Field
            letsbonk_url = f"https://letsbonk.fun/token/{address}"
            dexscreener_url = f"https://dexscreener.com/solana/{address}"
            solscan_url = f"https://solscan.io/token/{address}"
            
            links_value = (
                f"[LetsBonk.fun]({letsbonk_url})\n"
                f"[DexScreener]({dexscreener_url})\n"
                f"[SolScan]({solscan_url})"
            )
            
            embed.add_embed_field(
                name="🔗 Trading Links",
                value=links_value,
                inline=False
            )
            
            # Add extracted social media links if available
            social_links = token_data.get('social_links', [])
            if social_links:
                social_text = ""
                for link in social_links[:5]:  # Limit to 5 links to avoid spam
                    if "x.com" in link or "twitter.com" in link:
                        social_text += f"[Twitter/X]({link})\n"
                    elif "tiktok.com" in link:
                        social_text += f"[TikTok]({link})\n"
                    elif "t.me" in link:
                        social_text += f"[Telegram]({link})\n"
                    elif "discord" in link:
                        social_text += f"[Discord]({link})\n"
                    elif "instagram.com" in link:
                        social_text += f"[Instagram]({link})\n"
                    elif "youtube.com" in link:
                        social_text += f"[YouTube]({link})\n"
                    else:
                        # Generic social link
                        domain = link.split("//")[-1].split("/")[0]
                        social_text += f"[{domain}]({link})\n"
                
                if social_text:
                    embed.add_embed_field(
                        name="📱 Social Media Links",
                        value=social_text.strip(),
                        inline=False
                    )
            
            # Add Related Coins Field if keyword match found
            if matched_keyword:
                try:
                    from market_data_api import get_market_data_api
                    market_api = get_market_data_api()
                    related_tokens = market_api.search_related_tokens_by_keyword(matched_keyword, limit=3)
                    
                    if related_tokens:
                        related_value = ""
                        for i, token in enumerate(related_tokens, 1):
                            name = token['name'][:25]  # Allow slightly longer names
                            symbol = token['symbol']
                            mc = token['market_cap']
                            volume = token.get('volume_24h', 0)
                            address = token['address']
                            
                            # Format market cap display
                            if mc >= 1_000_000:
                                mc_display = f"${mc/1_000_000:.1f}M"
                            elif mc >= 1_000:
                                mc_display = f"${mc/1_000:.0f}K"
                            else:
                                mc_display = f"${mc:.0f}"
                            
                            # Format volume display
                            if volume >= 1_000_000:
                                vol_display = f"${volume/1_000_000:.1f}M"
                            elif volume >= 1_000:
                                vol_display = f"${volume/1_000:.0f}K"
                            else:
                                vol_display = f"${volume:.0f}"
                            
                            dex_url = f"https://dexscreener.com/solana/{address}"
                            related_value += f"**{i}.** [{name}]({dex_url}) ({symbol})\n"
                            related_value += f"    💰 MC: {mc_display} | 📊 Vol: {vol_display}\n"
                        
                        embed.add_embed_field(
                            name=f"🚀 Established '{matched_keyword}' Tokens (Higher Market Caps)",
                            value=related_value.strip(),
                            inline=False
                        )
                        logger.info(f"Added {len(related_tokens)} established related tokens for keyword: {matched_keyword}")
                    else:
                        logger.debug(f"No established related tokens found for keyword: {matched_keyword}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch related tokens for '{matched_keyword}': {e}")
            
            # Contract Address Field
            embed.add_embed_field(
                name="📄 Contract Address",
                value=f"`{address}`",
                inline=False
            )
            
            # Footer with detection info
            embed.set_footer(text=f"Alchemy API (FREE) • Detected: {age_display}")
            embed.set_timestamp()
            
            webhook.add_embed(embed)
            
            # Execute webhook with retry logic
            for attempt in range(Config.MAX_RETRIES):
                try:
                    response = webhook.execute()
                    
                    if response.status_code in [200, 204]:
                        logger.info(f"Successfully sent enhanced Discord notification for {address}")
                        return True
                    elif response.status_code == 429:
                        # Rate limited by Discord
                        retry_after = response.headers.get('Retry-After', 5)
                        logger.warning(f"Discord rate limit hit, waiting {retry_after} seconds")
                        time.sleep(int(retry_after))
                        continue
                    else:
                        logger.warning(f"Discord webhook returned status {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Discord webhook attempt {attempt + 1} failed: {e}")
                    
                # Wait before retry
                if attempt < Config.MAX_RETRIES - 1:
                    sleep_time = Config.RETRY_DELAY * (2 ** attempt)
                    time.sleep(sleep_time)
                    
            logger.error(f"Failed to send Discord notification after {Config.MAX_RETRIES} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False

    def send_contract_address(self, contract_address: str, coin_name: str = "", token_data: dict = None) -> bool:
        """
        Send a contract address to Discord.
        
        Args:
            contract_address: The contract address to send
            coin_name: Optional coin name for context
            token_data: Optional token data for age validation
            
        Returns:
            True if successful, False otherwise
        """
        # EMERGENCY NUCLEAR BLOCK: Validate token age before ANY notification
        blocked_tokens = [
            "EK7Ko9zmrfanDz98UnbWB9zkDPFV3Mcpx84t1DS2bonk",
            "7Zje1wV3r5sq8JEvJ1jFWifmSZe6CSBLRz4prFSXbonk", 
            "AHX7mj5Re2AwfvDgQUdVqEidQKHfH4tuxhdaLyLnbonk",
            "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",
            "4EPMN1CVGmWmxF4bBP4Nt4TjD2m5KTjWGMDDrt38bonk",
            "3ZWWatVxckSWHm1avfC5UFyHa4nN9x46KfhWq4Tqbonk"
        ]
        
        if contract_address in blocked_tokens:
            logger.error(f"🚨🚨🚨 SEND_CONTRACT_ADDRESS EMERGENCY BLOCK: {contract_address} is BLOCKED")
            logger.error(f"   🚫 Token: {coin_name} - USER COMPLAINED ABOUT THIS TOKEN")
            return False
        
        # NUCLEAR AGE VALIDATION in send_contract_address
        if token_data:
            import time
            created_timestamp = token_data.get('created_timestamp')
            if created_timestamp:
                current_time = time.time()
                if created_timestamp > 1e12:  # Handle milliseconds
                    created_timestamp = created_timestamp / 1000.0
                age_seconds = current_time - created_timestamp
                
                if age_seconds > 60:  # 60-second nuclear limit
                    age_hours = age_seconds / 3600
                    logger.error(f"🚫 SEND_CONTRACT_ADDRESS NUCLEAR BLOCK: {coin_name} is {age_hours:.1f} HOURS OLD")
                    logger.error(f"   📅 Created: {created_timestamp}, Current: {current_time}, Age: {age_seconds:.0f}s")
                    logger.error(f"   ⚠️ BLOCKING NOTIFICATION TO PREVENT USER COMPLAINT")
                    return False
        
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
            
        try:
            self._rate_limit()
            
            # Create webhook
            webhook = DiscordWebhook(url=self.webhook_url)
            
            # Format message based on configuration
            if Config.DISCORD_SEND_EMBED:
                # Send as embed for richer formatting
                embed = DiscordEmbed(
                    title="🚀 New Coin Match Found!",
                    color=0x00FF00
                )
                
                embed.add_embed_field(
                    name="Contract Address",
                    value=f"`{contract_address}`",
                    inline=False
                )
                
                if coin_name:
                    embed.add_embed_field(
                        name="Coin Name",
                        value=coin_name,
                        inline=False
                    )
                    
                # Add timestamp
                embed.set_timestamp()
                
                webhook.add_embed(embed)
                
            else:
                # Send as simple text message
                if coin_name:
                    message = f"🚀 **New Coin Match:** {coin_name}\n📄 **Contract:** `{contract_address}`"
                else:
                    message = f"🚀 **Contract Address:** `{contract_address}`"
                    
                webhook.content = message
            
            # Execute webhook with retry logic
            for attempt in range(Config.MAX_RETRIES):
                try:
                    response = webhook.execute()
                    
                    if response.status_code in [200, 204]:
                        logger.info(f"Successfully sent Discord notification for {contract_address}")
                        return True
                    elif response.status_code == 429:
                        # Rate limited by Discord
                        retry_after = response.headers.get('Retry-After', 5)
                        logger.warning(f"Discord rate limit hit, waiting {retry_after} seconds")
                        time.sleep(int(retry_after))
                        continue
                    else:
                        logger.warning(f"Discord webhook returned status {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Discord webhook attempt {attempt + 1} failed: {e}")
                    
                # Wait before retry
                if attempt < Config.MAX_RETRIES - 1:
                    sleep_time = Config.RETRY_DELAY * (2 ** attempt)
                    time.sleep(sleep_time)
                    
            logger.error(f"Failed to send Discord notification after {Config.MAX_RETRIES} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False
            
    def send_status_message(self, message: str) -> bool:
        """
        Send a status/info message to Discord.
        
        Args:
            message: Status message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
            
        try:
            self._rate_limit()
            
            webhook = DiscordWebhook(url=self.webhook_url)
            webhook.content = f"ℹ️ **Status:** {message}"
            
            response = webhook.execute()
            
            if response.status_code in [200, 204]:
                logger.info("Successfully sent status message to Discord")
                return True
            else:
                logger.warning(f"Discord status message returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Discord status message: {e}")
            return False
            
    def test_webhook(self) -> bool:
        """
        Test the Discord webhook connection.
        
        Returns:
            True if webhook is working, False otherwise
        """
        return self.send_status_message("Pump.fun monitor test - webhook is working! 🎉")
    
    async def send_embed_async(self, embed_data: dict) -> bool:
        """Send Discord embed notification asynchronously"""
        try:
            if not self.webhook_url:
                logger.error("Discord webhook URL not configured")
                return False
            
            # Rate limiting
            self._rate_limit()
            
            # Create webhook and embed
            webhook = DiscordWebhook(url=self.webhook_url)
            
            # Create embed from data
            embed = DiscordEmbed(
                title=embed_data.get('title', ''),
                description=embed_data.get('description', ''),
                color=embed_data.get('color', 0x00ff00)
            )
            
            # Add fields
            for field in embed_data.get('fields', []):
                embed.add_embed_field(
                    name=field['name'],
                    value=field['value'],
                    inline=field.get('inline', False)
                )
            
            # Set footer and timestamp
            if embed_data.get('footer'):
                embed.set_footer(text=embed_data['footer']['text'])
            
            if embed_data.get('timestamp'):
                embed.set_timestamp(embed_data['timestamp'])
            
            webhook.add_embed(embed)
            
            # Execute webhook
            response = webhook.execute()
            
            if response.status_code in [200, 204]:
                logger.info("✅ Discord embed notification sent successfully")
                return True
            else:
                logger.error(f"❌ Discord embed notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Discord embed notification error: {e}")
            return False
