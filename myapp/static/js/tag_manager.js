class TagManager {
    static init(config) {
        this.input = document.querySelector(config.inputSelector);
        this.addButton = document.querySelector(config.addButtonSelector);
        this.container = document.querySelector(config.containerSelector);
        this.hiddenTagNames = document.querySelector(config.hiddenTagNamesSelector);
        this.maxTags = config.maxTags || 8;

        this.tags = config.initialTags || [];
        this.tags.forEach(tag => this.addTagElement(tag));

        this.addButton.addEventListener('click', () => this.addTagFromInput());
        this.input.addEventListener('keypress', e => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTagFromInput();
            }
        });

        const form = this.input.closest('form');
        form.addEventListener('submit', () => {
            
            this.hiddenTagNames.value = this.tags.join(',');
        });
    }

    static addTagFromInput() {
        const newTag = this.input.value.trim();
        if (newTag && !this.tags.includes(newTag)) {
            if (this.tags.length < this.maxTags) {
                this.tags.push(newTag);
                this.addTagElement(newTag);
            } else {
                alert(`You can select up to ${this.maxTags} tags.`);
            }
        }
        this.input.value = '';
    }

    static addTagElement(tag) {
        const chip = document.createElement('span');
        chip.className = 'inline-flex items-center bg-gray-200 text-gray-800 text-sm rounded px-2 py-1';
        chip.textContent = tag;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'ml-2 text-gray-600 hover:text-gray-900 focus:outline-none';
        removeBtn.innerHTML = '&times;';
        removeBtn.addEventListener('click', () => this.removeTag(tag, chip));

        chip.appendChild(removeBtn);
        this.container.appendChild(chip);
    }

    static removeTag(tag, chipElement) {
        this.tags = this.tags.filter(t => t !== tag);
        chipElement.remove();
    }
}
