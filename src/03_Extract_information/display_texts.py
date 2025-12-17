#### 01_Product_extraction

def product_extraction_result(total_articles,articles_with_products,title_product_count,abstract_product_count,full_text_product_count):
    text= f"""
            <div class="alert alert-info" style="padding:15px; border-radius:5px; border-left:5px solid #17a2b8; background-color:#d1ecf1;">
            <h4 style="margin-top:0; color:#0c5460;">🔍 Product Extraction Pipeline</h4>
            <p style="margin-bottom:0; color:#0c5460;">We extracted products from titles, abstracts, and full text in three sequential passes</p>
            </div>

            <div style="margin-top:20px;">
            <h3>Extraction Results</h3>

            <p>We obtained <b>{total_articles:,}</b> relevant papers after filtering out reviews.</p>

            <p>From these, we successfully extracted products from <b>{articles_with_products:,}</b> papers:</p>

            <ul>
            <li>🏷️ <b>{title_product_count:,}</b> from titles</li>
            <li>📝 <b>{abstract_product_count:,}</b> from abstracts</li>  
            <li>📄 <b>{full_text_product_count:,}</b> from full text</li>
            </ul>

            <p><b>Success rate: {articles_with_products/total_articles:.1%}</b> of articles yielded product information.</p>
            </div>
            """
    return (text)

def product_extraction_summary(total_articles, articles_with_products, title_product_count, abstract_product_count, full_text_product_count, output_file):
        
    text = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #002b36; color: #93a1a1; padding: 20px; border-radius: 8px; margin: 10px 0; line-height: 1.6;">

    <!-- Header -->
    <div style="color: #b58900; font-weight: bold; font-size: 1.2em; border-bottom: 2px solid #586e75; padding-bottom: 10px; margin-bottom: 20px;">
        🧪 PRODUCT EXTRACTION PIPELINE - RESULTS
    </div>

    <!-- Process Flow -->
    <div style="margin-bottom: 20px; color: #859900; font-style: italic;">
        <span style="color: #268bd2;">→</span> Completed: Title → Abstract → Full Text
        <br>
        <span style="color: #268bd2;">→</span> Next Step: Product Cleaning & Validation
    </div>

    <!-- Summary Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #268bd2;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">📊 SUMMARY</div>
        <div style="margin-left: 10px;">
            <div style="margin-bottom: 5px;"><span style="color: #859900;">•</span> Articles Processed: <b style="color: #eee8d5;">{total_articles:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">•</span> Articles with Products: <b style="color: #eee8d5;">{articles_with_products:,}</b></div>
            <div><span style="color: #859900;">•</span> Success Rate: <b style="color: #eee8d5;">{articles_with_products/total_articles:.1%}</b></div>
        </div>
    </div>

    <!-- Breakdown Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #859900;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">🎯 BREAKDOWN BY SOURCE</div>
        <div style="margin-left: 10px;">
            <div style="margin-bottom: 5px;"><span style="color: #859900;">🏷️</span> Title: <b style="color: #eee8d5;">{title_product_count:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">📝</span> Abstract: <b style="color: #eee8d5;">{abstract_product_count:,}</b></div>
            <div><span style="color: #859900;">📄</span> Full Text: <b style="color: #eee8d5;">{full_text_product_count:,}</b></div>
        </div>
    </div>

    <!-- Output Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #b58900;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">💾 OUTPUT</div>
        <div style="margin-left: 10px; color: #859900;">
            Results saved to: <b style="color: #eee8d5;">{output_file}</b>
        </div>
    </div>

    <!-- Next Steps Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #cb4b16;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">🔜 NEXT STEP</div>
        <div style="margin-left: 10px; color: #859900;">
            The raw product list will now be cleaned to:
            <div style="margin-left: 15px; margin-top: 5px;">
                <span style="color: #859900;">•</span> Remove false positives & invalid entries<br>
                <span style="color: #859900;">•</span> Standardize naming conventions<br>
                <span style="color: #859900;">•</span> Separate combined product mentions
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div style="color: #859900; border-top: 2px solid #586e75; padding-top: 15px; margin-top: 20px; font-size: 12px; text-align: center;">
        ✅ Extraction complete. Ready for cleaning phase.
    </div>

</div>
"""
    
    return text



#### 02_Product_cleanup 


import pandas as pd
import numpy as np

def compute_cleanup_metrics(df):
    metrics = {}

    # Articles
    metrics['n_articles_total'] = df.shape[0]
    metrics['n_articles_before'] = df['Separated_products'].notna().sum()
    metrics['n_articles_after'] = df['Acid_antibiotic_normalized_cleaned'].notna().sum()
    metrics['n_articles_lost_all'] = metrics['n_articles_before'] - metrics['n_articles_after']

    # FIXED: Products before cleanup - count total product entries across all articles
    metrics['n_products_before'] = df['Separated_products'].dropna().apply(len).sum()

    # FIXED: Products after cleanup - count total product entries across all articles
    metrics['n_products_after'] = df['Acid_antibiotic_normalized_cleaned'].dropna().apply(len).sum()

    # Count removed and added
    removed, added, split, reduced, unchanged, normalized = 0, 0, 0, 0, 0, 0

    for before, after in zip(df['Separated_products'], df['Acid_antibiotic_normalized_cleaned']):
        # Handle NaN values
        if not isinstance(before, list):
            before = []
        if not isinstance(after, list):
            after = []
        
        # FIXED: Skip articles that had no products to begin with for case analysis
        # We still count removed/added for all articles
        before_set = set(before)
        after_set = set(after)

        removed_here = before_set - after_set
        added_here = after_set - before_set

        removed += len(removed_here)
        added += len(added_here)

        # Only analyze cases where there were products initially
        if before:  # This article had products before cleanup
            if len(after) > len(before):
                split += 1
            elif len(after) < len(before):
                reduced += 1
            else:  # same length
                if before == after:
                    unchanged += 1
                else:
                    normalized += 1  # same length but different content

    metrics['n_removed_total'] = removed
    metrics['n_added_total'] = added
    metrics['n_net_change'] = metrics['n_products_after'] - metrics['n_products_before']
    metrics['n_split'] = split
    metrics['n_reduced'] = reduced
    metrics['n_unchanged'] = unchanged
    metrics['n_normalized'] = normalized

    return metrics


def product_cleanup_summary(metrics, output_file):
    # Calculate article success rate (articles retained after cleanup)
    success_rate = 0
    if metrics['n_articles_before'] > 0:
        success_rate = metrics['n_articles_after'] / metrics['n_articles_before']

    # Net product change percentage
    net_change_pct = 0
    if metrics['n_products_before'] > 0:
        net_change_pct = metrics['n_net_change'] / metrics['n_products_before']

    # Additional helpful metrics
    avg_products_per_article_before = 0
    if metrics['n_articles_before'] > 0:
        avg_products_per_article_before = metrics['n_products_before'] / metrics['n_articles_before']
    
    avg_products_per_article_after = 0
    if metrics['n_articles_after'] > 0:
        avg_products_per_article_after = metrics['n_products_after'] / metrics['n_articles_after']
    
    # Calculate case percentages for better insight
    total_cases = metrics['n_split'] + metrics['n_reduced'] + metrics['n_unchanged'] + metrics['n_normalized']
    split_pct = (metrics['n_split'] / total_cases * 100) if total_cases > 0 else 0
    reduced_pct = (metrics['n_reduced'] / total_cases * 100) if total_cases > 0 else 0
    unchanged_pct = (metrics['n_unchanged'] / total_cases * 100) if total_cases > 0 else 0
    normalized_pct = (metrics['n_normalized'] / total_cases * 100) if total_cases > 0 else 0

    text = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #002b36; color: #93a1a1; padding: 20px; border-radius: 8px; margin: 10px 0; line-height: 1.6;">

    <!-- Header -->
    <div style="color: #b58900; font-weight: bold; font-size: 1.2em; border-bottom: 2px solid #586e75; padding-bottom: 10px; margin-bottom: 20px;">
        🧹 PRODUCT CLEANUP PIPELINE - RESULTS
    </div>

    <!-- Process Flow -->
    <div style="margin-bottom: 20px; color: #859900; font-style: italic;">
        <span style="color: #268bd2;">→</span> Completed: Extraction → Cleanup
        <br>
        <span style="color: #268bd2;">→</span> Next Step: Normalization & Deduplication
    </div>

    <!-- Summary Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #268bd2;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">📊 SUMMARY</div>
        <div style="margin-left: 10px;">
            <div style="margin-bottom: 5px;"><span style="color: #859900;">•</span> Total Articles: <b style="color: #eee8d5;">{metrics['n_articles_total']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">•</span> Articles w/ Products (before cleanup): <b style="color: #eee8d5;">{metrics['n_articles_before']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">•</span> Articles w/ Products (after cleanup): <b style="color: #eee8d5;">{metrics['n_articles_after']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">•</span> Lost All Products: <b style="color: #eee8d5;">{metrics['n_articles_lost_all']:,}</b></div>
            <div><span style="color: #859900;">•</span> Success Rate: <b style="color: #eee8d5;">{success_rate:.1%}</b></div>
        </div>
    </div>

    <!-- Breakdown Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #859900;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">🎯 PRODUCT BREAKDOWN</div>
        <div style="margin-left: 10px;">
            <div style="margin-bottom: 5px;"><span style="color: #859900;">📦</span> Products Before: <b style="color: #eee8d5;">{metrics['n_products_before']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">✅</span> Products After: <b style="color: #eee8d5;">{metrics['n_products_after']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">➕</span> Added (splits/normalization): <b style="color: #eee8d5;">{metrics['n_added_total']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">🗑️</span> Removed: <b style="color: #eee8d5;">{metrics['n_removed_total']:,}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">⚖️</span> Net Change: <b style="color: #eee8d5;">{metrics['n_net_change']:,} ({net_change_pct:+.1%})</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">📊</span> Avg Products/Article (before): <b style="color: #eee8d5;">{avg_products_per_article_before:.2f}</b></div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">📊</span> Avg Products/Article (after): <b style="color: #eee8d5;">{avg_products_per_article_after:.2f}</b></div>
        </div>
    </div>

    <!-- Case Analysis Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #b58900;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">🔍 CASE ANALYSIS ({total_cases:,} articles with products)</div>
        <div style="margin-left: 10px;">
            <div style="margin-bottom: 5px;"><span style="color: #859900;">✂️</span> Split Cases: <b style="color: #eee8d5;">{metrics['n_split']:,}</b> ({split_pct:.1f}%)</div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">➖</span> Reduced Cases: <b style="color: #eee8d5;">{metrics['n_reduced']:,}</b> ({reduced_pct:.1f}%)</div>
            <div style="margin-bottom: 5px;"><span style="color: #859900;">🔄</span> Normalized Cases: <b style="color: #eee8d5;">{metrics['n_normalized']:,}</b> ({normalized_pct:.1f}%)</div>
            <div><span style="color: #859900;">➖</span> Unchanged Cases: <b style="color: #eee8d5;">{metrics['n_unchanged']:,}</b> ({unchanged_pct:.1f}%)</div>
        </div>
    </div>

    <!-- Output Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #cb4b16;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">💾 OUTPUT</div>
        <div style="margin-left: 10px; color: #859900;">
            Cleaned results saved to: <b style="color: #eee8d5;">{output_file}</b>
        </div>
    </div>

    <!-- Next Steps Card -->
    <div style="margin: 15px 0; padding: 15px; background-color: #073642; border-radius: 5px; border-left: 4px solid #6c71c4;">
        <div style="color: #268bd2; font-weight: bold; margin-bottom: 10px;">🔜 NEXT STEP</div>
        <div style="margin-left: 10px; color: #859900;">
            The cleaned product list will now be normalized to:
            <div style="margin-left: 15px; margin-top: 5px;">
                <span style="color: #859900;">•</span> Standardize naming conventions<br>
                <span style="color: #859900;">•</span> Merge duplicates & synonyms<br>
                <span style="color: #859900;">•</span> Ensure consistency across sources
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div style="color: #859900; border-top: 2px solid #586e75; padding-top: 15px; margin-top: 20px; font-size: 12px; text-align: center;">
        ✅ Cleanup complete. {metrics['n_articles_after']:,} articles with {metrics['n_products_after']:,} product entries ready for normalization.
    </div>

</div>
"""
    return text