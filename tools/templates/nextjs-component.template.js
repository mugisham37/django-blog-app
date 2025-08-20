#!/usr/bin/env node
/**
 * Next.js Component Template Generator
 * 
 * This template generates Next.js components with:
 * - TypeScript support
 * - Tailwind CSS styling
 * - Proper prop types and interfaces
 * - Storybook stories
 * - Unit tests with React Testing Library
 * - Accessibility features
 */

const fs = require('fs');
const path = require('path');

class NextJSComponentTemplate {
  constructor(componentName, componentConfig) {
    this.componentName = componentName;
    this.config = componentConfig;
    this.componentPath = path.join('apps/web/src/components', this.config.category || 'common');
  }

  generateComponent() {
    console.log(`Generating Next.js component: ${this.componentName}`);
    
    // Create component directory
    this.createDirectoryStructure();
    
    // Generate files
    this.generateComponentFile();
    this.generateIndexFile();
    this.generateTypesFile();
    this.generateStorybookStory();
    this.generateTests();
    this.generateStyles();
    
    console.log(`Component '${this.componentName}' generated successfully!`);
  }

  createDirectoryStructure() {
    const componentDir = path.join(this.componentPath, this.componentName);
    
    if (!fs.existsSync(componentDir)) {
      fs.mkdirSync(componentDir, { recursive: true });
    }
    
    // Create subdirectories if needed
    const subdirs = ['__tests__', '__stories__'];
    subdirs.forEach(subdir => {
      const subdirPath = path.join(componentDir, subdir);
      if (!fs.existsSync(subdirPath)) {
        fs.mkdirSync(subdirPath, { recursive: true });
      }
    });
  }

  generateComponentFile() {
    const componentType = this.config.type || 'functional';
    const hasState = this.config.hasState || false;
    const hasEffects = this.config.hasEffects || false;
    
    let imports = `import React${hasState || hasEffects ? ', { useState, useEffect }' : ''} from 'react';
import { cn } from '@/lib/utils';`;
    
    if (this.config.useApiClient) {
      imports += `\nimport { useApiClient } from '@/hooks/useApiClient';`;
    }
    
    if (this.config.useRouter) {
      imports += `\nimport { useRouter } from 'next/navigation';`;
    }
    
    imports += `\nimport { ${this.componentName}Props } from './types';`;
    
    // Generate component body
    let componentBody = '';
    
    if (hasState) {
      componentBody += `  const [state, setState] = useState(${this.config.initialState || 'null'});\n\n`;
    }
    
    if (hasEffects) {
      componentBody += `  useEffect(() => {
    // Effect logic here
  }, []);

`;
    }
    
    if (this.config.useApiClient) {
      componentBody += `  const apiClient = useApiClient();

`;
    }
    
    if (this.config.useRouter) {
      componentBody += `  const router = useRouter();

`;
    }
    
    // Generate event handlers
    const handlers = this.config.handlers || [];
    handlers.forEach(handler => {
      componentBody += `  const handle${handler.charAt(0).toUpperCase() + handler.slice(1)} = (${handler.params || ''}) => {
    ${handler.body || '// Handler logic here'}
  };

`;
    });
    
    // Generate render logic
    const renderLogic = this.generateRenderLogic();
    
    const content = `${imports}

/**
 * ${this.componentName} Component
 * 
 * ${this.config.description || `A reusable ${this.componentName} component`}
 */
export const ${this.componentName}: React.FC<${this.componentName}Props> = ({
  ${this.generatePropsDestructuring()}
}) => {
${componentBody}  return (
${renderLogic}
  );
};

${this.componentName}.displayName = '${this.componentName}';

export default ${this.componentName};
`;

    const componentFile = path.join(this.componentPath, this.componentName, `${this.componentName}.tsx`);
    fs.writeFileSync(componentFile, content);
  }

  generatePropsDestructuring() {
    const props = this.config.props || {};
    const propNames = Object.keys(props);
    
    if (propNames.length === 0) {
      return 'className, ...props';
    }
    
    const destructured = propNames.map(prop => {
      const propConfig = props[prop];
      if (propConfig.default !== undefined) {
        return `${prop} = ${JSON.stringify(propConfig.default)}`;
      }
      return prop;
    });
    
    destructured.push('className', '...props');
    
    return destructured.join(',\n  ');
  }

  generateRenderLogic() {
    const variant = this.config.variant || 'div';
    const hasChildren = this.config.hasChildren !== false;
    
    let className = 'className';
    if (this.config.baseClasses) {
      className = `cn('${this.config.baseClasses}', className)`;
    }
    
    let attributes = `className={${className}}`;
    
    // Add accessibility attributes
    if (this.config.accessibility) {
      const a11y = this.config.accessibility;
      if (a11y.role) attributes += `\n      role="${a11y.role}"`;
      if (a11y.ariaLabel) attributes += `\n      aria-label={${a11y.ariaLabel}}`;
      if (a11y.ariaDescribedBy) attributes += `\n      aria-describedby={${a11y.ariaDescribedBy}}`;
    }
    
    // Add event handlers
    const handlers = this.config.handlers || [];
    handlers.forEach(handler => {
      attributes += `\n      on${handler.charAt(0).toUpperCase() + handler.slice(1)}={handle${handler.charAt(0).toUpperCase() + handler.slice(1)}}`;
    });
    
    attributes += '\n      {...props}';
    
    let content = '';
    if (this.config.content) {
      content = this.config.content;
    } else if (hasChildren) {
      content = '{children}';
    } else {
      content = `{${this.config.defaultContent || 'content'}}`;
    }
    
    return `    <${variant}
      ${attributes}
    >
      ${content}
    </${variant}>`;
  }

  generateIndexFile() {
    const content = `export { ${this.componentName} } from './${this.componentName}';
export type { ${this.componentName}Props } from './types';
export default ${this.componentName};
`;

    const indexFile = path.join(this.componentPath, this.componentName, 'index.ts');
    fs.writeFileSync(indexFile, content);
  }

  generateTypesFile() {
    const props = this.config.props || {};
    const propTypes = Object.entries(props).map(([name, config]) => {
      const optional = config.required === false ? '?' : '';
      const type = config.type || 'string';
      const comment = config.description ? `  /** ${config.description} */\n` : '';
      
      return `${comment}  ${name}${optional}: ${type};`;
    }).join('\n');
    
    const baseProps = this.config.extendsHtmlElement !== false 
      ? ` & React.HTMLAttributes<HTML${this.config.htmlElement || 'Div'}Element>`
      : '';
    
    const content = `import React from 'react';

export interface ${this.componentName}Props${baseProps} {
${propTypes}
${this.config.hasChildren !== false ? '  /** Child elements */\n  children?: React.ReactNode;' : ''}
${this.config.customClassName !== false ? '  /** Additional CSS classes */\n  className?: string;' : ''}
}

${this.generateAdditionalTypes()}
`;

    const typesFile = path.join(this.componentPath, this.componentName, 'types.ts');
    fs.writeFileSync(typesFile, content);
  }

  generateAdditionalTypes() {
    const additionalTypes = this.config.additionalTypes || [];
    
    return additionalTypes.map(type => {
      if (typeof type === 'string') {
        return `export type ${type} = string;`;
      }
      
      return `export interface ${type.name} {
${Object.entries(type.properties || {}).map(([prop, propType]) => 
  `  ${prop}: ${propType};`
).join('\n')}
}`;
    }).join('\n\n');
  }

  generateStorybookStory() {
    const props = this.config.props || {};
    const defaultArgs = Object.entries(props).reduce((acc, [name, config]) => {
      if (config.default !== undefined) {
        acc[name] = config.default;
      }
      return acc;
    }, {});
    
    if (this.config.hasChildren !== false) {
      defaultArgs.children = this.config.defaultChildren || `${this.componentName} Content`;
    }
    
    const content = `import type { Meta, StoryObj } from '@storybook/react';
import { ${this.componentName} } from './${this.componentName}';

const meta: Meta<typeof ${this.componentName}> = {
  title: '${this.config.storybookCategory || 'Components'}/${this.componentName}',
  component: ${this.componentName},
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '${this.config.description || `A reusable ${this.componentName} component`}',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
${this.generateStorybookArgTypes()}
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: ${JSON.stringify(defaultArgs, null, 4)},
};

${this.generateStorybookVariants()}
`;

    const storyFile = path.join(this.componentPath, this.componentName, '__stories__', `${this.componentName}.stories.tsx`);
    fs.writeFileSync(storyFile, content);
  }

  generateStorybookArgTypes() {
    const props = this.config.props || {};
    
    return Object.entries(props).map(([name, config]) => {
      const argType = {
        description: config.description || `${name} prop`,
        control: config.control || 'text'
      };
      
      if (config.options) {
        argType.control = 'select';
        argType.options = config.options;
      }
      
      return `    ${name}: {
      description: '${argType.description}',
      control: '${argType.control}',${argType.options ? `\n      options: ${JSON.stringify(argType.options)},` : ''}
    }`;
    }).join(',\n');
  }

  generateStorybookVariants() {
    const variants = this.config.storybookVariants || [];
    
    return variants.map(variant => {
      return `export const ${variant.name}: Story = {
  args: ${JSON.stringify(variant.args, null, 4)},${variant.parameters ? `\n  parameters: ${JSON.stringify(variant.parameters, null, 4)},` : ''}
};`;
    }).join('\n\n');
  }

  generateTests() {
    const content = `import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ${this.componentName} } from '../${this.componentName}';

describe('${this.componentName}', () => {
  const defaultProps = {
${this.generateDefaultTestProps()}
  };

  it('renders without crashing', () => {
    render(<${this.componentName} {...defaultProps} />);
    expect(screen.getByRole('${this.config.testRole || 'generic'}')).toBeInTheDocument();
  });

${this.config.hasChildren !== false ? `  it('renders children correctly', () => {
    const testContent = 'Test Content';
    render(<${this.componentName} {...defaultProps}>{testContent}</${this.componentName}>);
    expect(screen.getByText(testContent)).toBeInTheDocument();
  });

` : ''}  it('applies custom className', () => {
    const customClass = 'custom-class';
    render(<${this.componentName} {...defaultProps} className={customClass} />);
    expect(screen.getByRole('${this.config.testRole || 'generic'}')).toHaveClass(customClass);
  });

${this.generateEventHandlerTests()}

  it('meets accessibility requirements', () => {
    render(<${this.componentName} {...defaultProps} />);
    const element = screen.getByRole('${this.config.testRole || 'generic'}');
    
    // Add specific accessibility tests based on component type
    expect(element).toBeVisible();
    ${this.config.accessibility?.ariaLabel ? `expect(element).toHaveAttribute('aria-label');` : ''}
  });
});
`;

    const testFile = path.join(this.componentPath, this.componentName, '__tests__', `${this.componentName}.test.tsx`);
    fs.writeFileSync(testFile, content);
  }

  generateDefaultTestProps() {
    const props = this.config.props || {};
    
    return Object.entries(props).map(([name, config]) => {
      const value = config.testValue || config.default || this.getDefaultTestValue(config.type);
      return `    ${name}: ${JSON.stringify(value)}`;
    }).join(',\n');
  }

  getDefaultTestValue(type) {
    const defaults = {
      'string': 'test',
      'number': 0,
      'boolean': false,
      'function': '() => {}',
      'object': '{}',
      'array': '[]'
    };
    
    return defaults[type] || 'test';
  }

  generateEventHandlerTests() {
    const handlers = this.config.handlers || [];
    
    return handlers.map(handler => {
      return `  it('handles ${handler} event', () => {
    const mock${handler.charAt(0).toUpperCase() + handler.slice(1)} = jest.fn();
    render(<${this.componentName} {...defaultProps} on${handler.charAt(0).toUpperCase() + handler.slice(1)}={mock${handler.charAt(0).toUpperCase() + handler.slice(1)}} />);
    
    const element = screen.getByRole('${this.config.testRole || 'generic'}');
    fireEvent.${handler}(element);
    
    expect(mock${handler.charAt(0).toUpperCase() + handler.slice(1)}).toHaveBeenCalledTimes(1);
  });

`;
    }).join('');
  }

  generateStyles() {
    if (!this.config.generateStyles) return;
    
    const content = `.${this.componentName.toLowerCase()} {
  /* Component-specific styles */
  ${this.config.baseStyles || ''}
}

.${this.componentName.toLowerCase()}--variant {
  /* Variant styles */
}

.${this.componentName.toLowerCase()}--disabled {
  /* Disabled state styles */
  opacity: 0.6;
  pointer-events: none;
}

@media (max-width: 768px) {
  .${this.componentName.toLowerCase()} {
    /* Mobile styles */
  }
}
`;

    const stylesFile = path.join(this.componentPath, this.componentName, `${this.componentName}.module.css`);
    fs.writeFileSync(stylesFile, content);
  }
}

// Example configurations
const EXAMPLE_CONFIGS = {
  button: {
    type: 'functional',
    category: 'ui',
    description: 'A reusable button component with multiple variants',
    hasChildren: true,
    variant: 'button',
    htmlElement: 'Button',
    baseClasses: 'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background',
    props: {
      variant: {
        type: "'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'",
        default: 'default',
        description: 'Button variant',
        control: 'select',
        options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link']
      },
      size: {
        type: "'default' | 'sm' | 'lg' | 'icon'",
        default: 'default',
        description: 'Button size',
        control: 'select',
        options: ['default', 'sm', 'lg', 'icon']
      },
      disabled: {
        type: 'boolean',
        default: false,
        description: 'Whether the button is disabled'
      }
    },
    handlers: ['click'],
    accessibility: {
      role: 'button'
    },
    testRole: 'button',
    storybookCategory: 'UI/Button',
    storybookVariants: [
      {
        name: 'Primary',
        args: { variant: 'default', children: 'Primary Button' }
      },
      {
        name: 'Secondary',
        args: { variant: 'secondary', children: 'Secondary Button' }
      },
      {
        name: 'Destructive',
        args: { variant: 'destructive', children: 'Delete' }
      }
    ]
  },
  
  card: {
    type: 'functional',
    category: 'ui',
    description: 'A flexible card component for displaying content',
    hasChildren: true,
    variant: 'div',
    baseClasses: 'rounded-lg border bg-card text-card-foreground shadow-sm',
    props: {
      title: {
        type: 'string',
        description: 'Card title',
        required: false
      },
      description: {
        type: 'string',
        description: 'Card description',
        required: false
      },
      footer: {
        type: 'React.ReactNode',
        description: 'Card footer content',
        required: false
      }
    },
    testRole: 'generic',
    storybookCategory: 'UI/Card'
  },
  
  modal: {
    type: 'functional',
    category: 'ui',
    description: 'A modal dialog component',
    hasChildren: true,
    hasState: true,
    hasEffects: true,
    variant: 'div',
    props: {
      isOpen: {
        type: 'boolean',
        default: false,
        description: 'Whether the modal is open'
      },
      onClose: {
        type: '() => void',
        description: 'Function to call when modal should close'
      },
      title: {
        type: 'string',
        description: 'Modal title'
      }
    },
    handlers: ['close'],
    accessibility: {
      role: 'dialog',
      ariaLabel: 'title'
    },
    testRole: 'dialog',
    storybookCategory: 'UI/Modal'
  }
};

function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 1) {
    console.log(`
Next.js Component Template Generator

Usage:
  node tools/templates/nextjs-component.template.js <component-name> [options]

Options:
  --config <path>     Path to JSON configuration file
  --preset <name>     Use predefined preset (button, card, modal)
  --help             Show this help message

Examples:
  node tools/templates/nextjs-component.template.js Button --preset button
  node tools/templates/nextjs-component.template.js CustomCard --config ./card-config.json
    `);
    return;
  }

  const componentName = args[0];
  let config = {};

  // Parse arguments
  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--config' && args[i + 1]) {
      const configPath = args[i + 1];
      config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      i++;
    } else if (args[i] === '--preset' && args[i + 1]) {
      const preset = args[i + 1];
      if (EXAMPLE_CONFIGS[preset]) {
        config = EXAMPLE_CONFIGS[preset];
      } else {
        console.error(`Unknown preset: ${preset}`);
        console.log(`Available presets: ${Object.keys(EXAMPLE_CONFIGS).join(', ')}`);
        return;
      }
      i++;
    }
  }

  const generator = new NextJSComponentTemplate(componentName, config);
  generator.generateComponent();
}

if (require.main === module) {
  main();
}

module.exports = { NextJSComponentTemplate, EXAMPLE_CONFIGS };