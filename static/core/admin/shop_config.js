/* shop_config.js */
document.addEventListener('DOMContentLoaded', function() {
    const fieldsets = document.querySelectorAll('#shopconfig_form fieldset');
    const contentMain = document.querySelector('#content-main form');
    const heroSlidesInline = document.querySelector('.inline-group');
    
    if (!fieldsets.length || !contentMain) return;

    // Create tab bar
    const tabBar = document.createElement('div');
    tabBar.className = 'tab-container';
    contentMain.insertBefore(tabBar, contentMain.firstChild);

    fieldsets.forEach((fieldset, index) => {
        // Skip inlines that might be inside fieldsets (rare but possible)
        if (fieldset.closest('.inline-group')) return;

        const titleElement = fieldset.querySelector('h2');
        if (!titleElement) return;

        const title = titleElement.innerText;
        fieldset.classList.add('tabbed');
        
        // Create button
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'tab-button';
        button.innerText = title;
        
        button.addEventListener('click', () => {
            // Deactivate all
            document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('fieldset.tabbed').forEach(f => f.classList.remove('active'));
            
            // Activate current
            button.classList.add('active');
            fieldset.classList.add('active');
            
            // Handle Hero Slides Inline
            if (heroSlidesInline) {
                if (title.includes('Hero')) {
                    heroSlidesInline.style.display = 'block';
                } else {
                    heroSlidesInline.style.display = 'none';
                }
            }
        });

        tabBar.appendChild(button);

        // Default to first tab
        if (index === 0) {
            button.classList.add('active');
            fieldset.classList.add('active');
        }
    });

    // Initial state for inlines
    if (heroSlidesInline) {
        const activeTab = document.querySelector('.tab-button.active');
        if (activeTab && !activeTab.innerText.includes('Hero')) {
            heroSlidesInline.style.display = 'none';
        }
        
        // Hide the internal H2 of the inline to avoid double titles
        const inlineH2 = heroSlidesInline.querySelector('h2');
        if (inlineH2) inlineH2.style.display = 'none';
    }
});
